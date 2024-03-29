import argparse
import datetime
import json
import yaml

from pathlib import Path

from google.cloud import pubsub_v1
from google.oauth2 import service_account
from google.cloud import storage

from tqdm import tqdm


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--maxmessages",
        required=False,
        type=int,
        default=10,
        help="maximum number of messages to send",
    )
    parser.add_argument(
        "--expiration",
        required=False,
        type=int,
        default=15,
        help="number of minutes to generate an expiration for the signed URL",
    )
    parser.add_argument(
        "--configfile",
        required=True,
        type=Path,
        help="path to the yaml config file",
    )

    args = parser.parse_args()
    with open(args.configfile, "r") as file:
        config = yaml.safe_load(file)

    # Get the contents of the bucket.
    creds_path = config["accounts"]["service_account"]["path_to_credentials"]
    source_credentials = service_account.Credentials.from_service_account_file(
        creds_path
    )
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
