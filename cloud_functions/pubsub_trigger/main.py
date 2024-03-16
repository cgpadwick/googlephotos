import base64
import os
from google.cloud import pubsub_v1


def hello_pubsub(event, context):
    """
    A function to handle a Pub/Sub event. It decodes the message from the event, sets up the Pub/Sub publisher client, and publishes the message to a specified topic.
    Parameters:
        event: dict, The Pub/Sub event data.
        context: google.cloud.functions.Context, The event metadata.
    Returns:
        None
    """

    message = base64.b64decode(event["data"]).decode("utf-8")

    publisher = pubsub_v1.PublisherClient()
    topic_name = f"projects/cgp-project/topics/cgp-processed-topic"
    msg = f"Received message: {message}"
    data = msg.encode("utf-8")
    future = publisher.publish(topic_name, data=data)
    future.result()
    print(msg)
    print(os.environ['OPENAI_API_KEY'])
