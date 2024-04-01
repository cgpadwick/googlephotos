import base64
from io import BytesIO
import json
from PIL import Image
from PIL.ExifTags import TAGS
import traceback
import uuid

import firebase_admin
from firebase_admin import firestore

from google.cloud import storage
from google.cloud import logging


def get_exif_data(blob):
    """Get Exif data from the blob object."""

    if "image" in blob.content_type:
        blob_data = blob.download_as_bytes()
        img = Image.open(BytesIO(blob_data))

        exif_data = img._getexif()

        if exif_data:
            exif_info = {}
            for tag, value in exif_data.items():
                tag_name = TAGS.get(tag, tag)
                exif_info[tag_name] = value
            return exif_info
        else:
            return {}


def insert_into_db(message, exif_data):
    """Insert record into the database."""

    database_name = message.get("database_name")
    tl_name = message.get("top_level_collection_name")
    sl_name = message.get("sub_level_collection_name")
    bucket_name = message.get("bucket_name")
    blob_name = message.get("blob_name")
    user_id = message.get("user_id")

    data_record = {
        "blob_name": blob_name,
        "bucket_name": bucket_name,
        "exif_data": exif_data,
        "uuid": uuid.uuid4(),
    }

    _ = firebase_admin.initialize_app()
    db = firestore.Client(database_name)

    log_message(data_record)

    doc_ref = (
        db.collection(tl_name)
        .document(user_id)
        .collection(sl_name)
        .document(str(data_record["uuid"]))
    )
    doc_ref.set(data_record)


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

        exif_data = get_exif_data(blob)
        insert_into_db(message, exif_data)

        log_message(
            {
                "message": "Ingested image", 
                "user_id": message["user_id"],
                "bucket_name": message["bucket_name"],
                "blob_name": message["blob_name"],
                "status": "success"
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
