import base64
from io import BytesIO
import json
import os
from PIL import Image
from pillow_heif import register_heif_opener
import requests
import traceback

import firebase_admin
from firebase_admin import firestore

from google.cloud import logging
from google.cloud import storage


def log_message(msg_dict):
    """Log message to Cloud Logging."""

    client = logging.Client()
    logger = client.logger("caption")
    logger.log_struct(msg_dict)


def generate_caption(doc_ref):
    """
    A function to predict captions for images from the given URL.

    :param image_url: The URL of the image to be processed
    :return: caption generated for the image.
    """

    doc = doc_ref.get().to_dict()
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(doc["bucket_name"])
    blob = bucket.get_blob(doc["blob_name"])

    register_heif_opener()  # Register the HEIF and HEIC support.
    blob_data = blob.download_as_bytes()
    img = Image.open(BytesIO(blob_data))
    img = img.convert("RGB")  # Handle PNG RGBA format.
    # If the image format isn't jpeg, convert it before sending it
    # to the captioning API.
    if img.format != "JPEG":
        bytes_buffer = BytesIO()
        img.save(bytes_buffer, "jpeg")
        img_bytes = base64.b64encode(bytes_buffer.getvalue()).decode("utf-8")
    else:
        img_bytes = base64.b64encode(blob_data).decode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
    }

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What’s in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_bytes}"},
                    },
                ],
            }
        ],
        "max_tokens": 300,
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
    )
    response.raise_for_status()
    caption = response.json()["choices"][0]["message"]["content"].strip()

    return caption


def get_docref_from_db(message):
    """Retrieve reference to a document from the database."""

    database_name = message.get("database_name")

    # Document path is intended to be in the format
    # "customers/{customer_id}/{tl_name}/{document_id}"
    document_path = message.get("document_path")

    if not firebase_admin._apps:
        _ = firebase_admin.initialize_app()

    db = firestore.Client(database=database_name)
    doc_ref = db.document(document_path)

    return doc_ref


def caption_image(event, context):
    """
    A function to process an image caption event.

    Parameters:
        event (dict): The event triggering the function.
        context (dict): The context in which the function is running.

    Returns:
        None
    """
    try:
        data = base64.b64decode(event["data"]).decode("utf-8")
        message = json.loads(data)

        doc_ref = get_docref_from_db(message)
        caption = generate_caption(doc_ref)
        doc_ref.update({"caption": caption})

        log_message(
            {
                "message": "Captioned image",
                "document_path": message["document_path"],
                "status": "success",
            }
        )

    except Exception as e:

        log_message(
            {
                "message": "Failed to caption image",
                "document_path": message["document_path"],
                "error": str(e),
                "traceback": traceback.format_exc(),
                "status": "error",
            }
        )
