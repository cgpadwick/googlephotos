import base64
import datetime
import json
import os
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


def predict_from_url(image_url):
    """
    A function to predict captions for images from the given URL.

    :param image_url: The URL of the image to be processed
    :return: caption generated for the image.
    """

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
                        "image_url": {"url": image_url},
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


def generate_signed_url(message):
    """Generate a signed URL for the image."""

    doc_ref = get_docref_from_db(message)
    doc = doc_ref.get().to_dict()

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(doc["bucket_name"])
    blob = bucket.get_blob(doc["blob_name"])

    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=5),
        method="GET",
    )

    return signed_url


def update_document_in_db(message, caption):
    """Insert record into the database."""

    doc_ref = get_docref_from_db(message)
    doc_ref.update({"caption": caption})


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

        url = generate_signed_url(message)
        caption = predict_from_url(url)
        update_document_in_db(message, caption)

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
