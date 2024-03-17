import base64
import json
import os
import requests
from google.cloud import pubsub_v1


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


def hello_pubsub(event, context):
    """
    A function to handle a Pub/Sub event. It decodes the message from the event, sets up the Pub/Sub publisher client, and publishes the message to a specified topic.
    Parameters:
        event: dict, The Pub/Sub event data.
        context: google.cloud.functions.Context, The event metadata.
    Returns:
        None
    """

    data = base64.b64decode(event["data"]).decode("utf-8")
    message = json.loads(data)
    baseurl = message.get("baseurl")
    caption = predict_from_url(baseurl)

    publisher = pubsub_v1.PublisherClient()
    topic_name = f"projects/cgp-project/topics/cgp-processed-topic"
    msg = f"Received message: {message}. caption: {caption}"
    data = msg.encode("utf-8")
    future = publisher.publish(topic_name, data=data)
    future.result()
    print(f'caption was: {caption}')
