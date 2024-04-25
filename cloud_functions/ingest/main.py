import base64
from datetime import datetime
from io import BytesIO
import json
import os
from PIL import Image, TiffImagePlugin
from PIL.ExifTags import TAGS
import piexif
from pillow_heif import register_heif_opener
import re
import traceback
import uuid

import firebase_admin
from firebase_admin import firestore

from google.cloud import storage
from google.cloud import logging


def generate_webp_image(bucket, blob, storage_client=None):
    """
    Generates a resized version of an image in WebP format and uploads it to the bucket.

    Parameters:
    - bucket: The storage bucket where the image will be uploaded.
    - blob: The image to be resized and converted.
    - storage_client: Optional. The storage client to use. If not provided, a new client will be created.

    Returns:
    - If the WebP version of the image was successfully generated and uploaded, returns the new blob name.
    - If the image already exists in WebP format, returns None.
    """

    if "image" in blob.content_type:

        # Set up the new blob name.
        base, _ = os.path.splitext(os.path.basename(blob.name))
        dir_name = os.path.dirname(blob.name)
        new_blob_name = os.path.join(dir_name, f"{base}.webp")

        # Check and see if it exists or not.
        if storage_client is None:
            storage_client = storage.Client()
        if not storage.Blob(bucket=bucket, name=new_blob_name).exists(storage_client):

            # Generate a resized version of the image in webp format
            # and upload it to the bucket.
            register_heif_opener()  # Register the HEIF and HEIC support.
            blob_data = blob.download_as_bytes()
            img = Image.open(BytesIO(blob_data))
            img = img.convert("RGB")  # Handle PNG RGBA format.
            w, h = img.size
            resize_factor = min(w, h) // 500
            if resize_factor < 1:
                resize_factor = 1

            bytes_buffer = BytesIO()
            img.resize((w // resize_factor, h // resize_factor), Image.LANCZOS).save(
                bytes_buffer, "WEBP"
            )
            del img
            bucket.blob(new_blob_name).upload_from_string(bytes_buffer.getvalue())

        return new_blob_name

    return None


def cast(v):
    """
    Casts the input value v to the appropriate type if necessary.

    Parameters:
    v : Any - The input value to be casted.

    Returns:
    Any - The casted value.
    """
    if isinstance(v, TiffImagePlugin.IFDRational):
        # Check for nan values here befoe casting to float.
        if v != v:
            return None
        else:
            return float(v)
    elif isinstance(v, tuple):
        return tuple(cast(t) for t in v)
    elif isinstance(v, bytes):
        return v.decode(errors="replace")
    elif isinstance(v, dict):
        for kk, vv in v.items():
            v[kk] = cast(vv)
        return v
    else:
        return v


def flatten_nested_tuples(t):
    """
    Flattens nested tuples in the input tuple 't'.

    Parameters:
    t : tuple - The input tuple to flatten.

    Returns:
    tuple - The flattened tuple or the original input tuple if it's not nested.
    """

    if isinstance(t, tuple):
        if len(t) != 0 and isinstance(t[0], tuple):
            return tuple([x for xs in t for x in xs])
    return t


def get_exif_data(blob):
    """Get Exif data from the blob object."""

    if "image" in blob.content_type:
        register_heif_opener()  # Register the HEIF and HEIC support.
        blob_data = blob.download_as_bytes()
        img = Image.open(BytesIO(blob_data))
        exif_data = {}

        if img.format == "BMP":
            # BMP images have no exif data and no exif tags are defined.
            # PIL doesn't handle this properly so we need to handle it manually.
            exif_data = {}
        elif img.format == "HEIC" or img.format == "HEIF":
            # Load the exif data from the image if it exists.
            raw_exif_data = img.info.get("exif", None)
            if raw_exif_data:
                result = piexif.load(raw_exif_data, key_is_name=True)
                exif_data = result.get("Exif", {})
        else:
            exif_data = img.getexif()

        if exif_data:
            exif_info = {}
            for tag, value in exif_data.items():
                tag_name = TAGS.get(tag, tag)
                exif_info[tag_name] = flatten_nested_tuples(cast(value))
            return exif_info
        else:
            return {}


def get_photo_acquired_time(blob_name, exif_data):
    """
    Get the acquired time of a photo based on the exif data and filename.

    Args:
    - blob_name: The name of the photo blob.
    - exif_data: The exif data of the photo.

    Returns:
    - The acquired time of the photo as a datetime object.
    """

    # If the exif data exists, read the field DateTimeOriginal as the timestamp.
    # If not, then look at the filename of the photo.  If it matches a format like
    # "20230525_192803.jpg" then that can be converted into a date.  If not then
    # set the creation date to a default value.

    default_timestamp = datetime(1970, 1, 1, 0, 0, 0)
    if exif_data:
        # Example value from DB: "2018:10:07 15:51:33"
        exif_datetime_str = exif_data.get("DateTimeOriginal", None)
        if exif_datetime_str:
            date_str = "%Y:%m:%d %H:%M:%S"
            time_stamp = datetime.strptime(exif_datetime_str, date_str)
            return time_stamp
    else:
        # Example filename: "20230525_192803.jpg"
        res = os.path.splitext(os.path.basename(blob_name))
        if len(res) == 2:
            base_str = res[0]
            pattern = r"^\d{4}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])_(0[0-9]|1[0-9]|2[0-3])([0-5]\d){2}$"
            if re.match(pattern, base_str):
                date_str = "%Y%m%d_%H%M%S"
                time_stamp = datetime.strptime(base_str, date_str)
                return time_stamp

    return default_timestamp


def insert_into_db(message, exif_data, time_stamp, webp_name):
    """Insert record into the database."""

    database_name = message.get("database_name")
    customer_table_name = message.get("customer_table_name")
    tl_name = message.get("top_level_collection_name")
    bucket_name = message.get("bucket_name")
    blob_name = message.get("blob_name")
    user_id = message.get("user_id")

    data_record = {
        "blob_name": blob_name,
        "bucket_name": bucket_name,
        "acquisition_time": time_stamp.isoformat(),
        "exif_data": exif_data,
        "uuid": str(uuid.uuid4()),
        "rr_img": webp_name,
    }

    # Convert any integer keys to strings.
    data_record = json.loads(json.dumps(data_record))

    if not firebase_admin._apps:
        _ = firebase_admin.initialize_app()

    db = firestore.Client(database=database_name)

    doc_ref = (
        db.collection(customer_table_name)
        .document(user_id)
        .collection(tl_name)
        .document(str(data_record["uuid"]))
    )
    doc_ref.set(data_record, merge=True)


def log_message(msg_dict):
    """Log message to Cloud Logging."""

    client = logging.Client()
    logger = client.logger("ingest")
    logger.log_struct(msg_dict)


def ingest_object(event, context):
    """
    A function to ingest an object, decode the data, retrieve information from a storage bucket,
    extract exif data, insert data into a database, and log messages.
    It takes 'event' and 'context' as parameters.
    """

    data = base64.b64decode(event["data"]).decode("utf-8")
    message = json.loads(data)

    try:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(message.get("bucket_name"))
        blob = bucket.get_blob(message.get("blob_name"))
        webp_name = generate_webp_image(bucket, blob, storage_client)
        exif_data = get_exif_data(blob)
        time_stamp = get_photo_acquired_time(message["blob_name"], exif_data)
        insert_into_db(message, exif_data, time_stamp, webp_name)

        log_message(
            {
                "message": "Ingested image",
                "user_id": message["user_id"],
                "bucket_name": message["bucket_name"],
                "blob_name": message["blob_name"],
                "status": "success",
            }
        )

    except Exception as e:
        log_message(
            {
                "message": "Failed to ingest image",
                "user_id": message["user_id"],
                "error": str(e),
                "traceback": traceback.format_exc(),
                "bucket_name": message["bucket_name"],
                "blob_name": message["blob_name"],
                "status": "error",
            }
        )
