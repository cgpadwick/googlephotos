import argparse
import datetime
import json
import yaml

from pathlib import Path

from google.oauth2 import service_account
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


from tqdm import tqdm


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--configfile",
        required=True,
        type=Path,
        help="path to the yaml config file",
    )

    args = parser.parse_args()
    with open(args.configfile, "r") as file:
        config = yaml.safe_load(file)

    # Firestore setup.
    creds_path = config["accounts"]["service_account"]["path_to_credentials"]
    creds = credentials.Certificate(creds_path)
    app = firebase_admin.initialize_app(creds)
    db = firestore.client()

    doc_ref = db.collection("users").document("alovelace")
    doc_ref.set({"first": "Ada", "last": "Lovelace", "born": 1815})


    storage_client = storage.Client(credentials=source_credentials)
    bucket = storage_client.get_bucket(config["buckets"]["main_bucket"]["name"])
    blobs = bucket.list_blobs()

    # Create the topic path
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(
        config["project_id"], config["topics"]["target_topic"]["name"]
    )

    # Iterate through the blobs and create messages for each.
    num_msgs_sent = 0
    for blob in tqdm(blobs):

        if "image" in blob.content_type:
            # Generate a signed URL with the specified expiration.
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.timedelta(minutes=args.expiration),
                method="GET",
            )
            msg = {
                "baseurl": signed_url,
                "id": blob.id,
                "project_id": config["project_id"],
                "processed_topic": config["topics"]["processed_topic"]["name"],
                "error_topic": config["topics"]["error_topic"]["name"],
            }
            message_data = json.dumps(msg).encode("utf-8")

            # Publish the message
            future = publisher.publish(topic_path, data=message_data)
            message_id = future.result()
            num_msgs_sent += 1

        if num_msgs_sent >= args.maxmessages:
            break
