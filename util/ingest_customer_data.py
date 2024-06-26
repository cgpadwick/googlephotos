import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, "../src")
import time
import yaml

from tqdm import tqdm

import photosapp


def ingest_data(config_file, email, maxmessages, test_mode=False):
    """
    Ingest data from a configuration file for a specific customer.

    Parameters:
    - config_file: str, the path to the configuration file
    - email: str, the email address of the customer
    - maxmessages: int, the maximum number of messages to process
    - test_mode: bool, optional, whether to run in test mode (default is False)

    Returns:
    This function does not return anything explicitly.
    """

    with open(config_file, "r") as file:
        config = yaml.safe_load(file)

    db_helper = photosapp.DatabaseHelper(config_file, test_mode)
    customer_rec = db_helper.get_customer(email)

    storage_helper = photosapp.GCStoragehelper(config_file)
    blobs = storage_helper.get_blobs(customer_rec["bucket_name"])

    pubsub_helper = photosapp.PubSubHelper(config_file)
    topic_name = config["topics"]["ingest_topic"]["name"]

    msg_batch_size = config["functions"]["ingest_function"]["max_instances"]

    db_name = config["firestore"]["database_name"]
    if test_mode:
        db_name = config["firestore"]["testdb_name"]

    # Iterate through the blobs and create messages for each.
    total_num_msgs_sent = 0
    for blob in tqdm(blobs):

        if "image" in blob.content_type:

            # Skip adding the reduced image if it already exists.
            base, ext = os.path.splitext(os.path.basename(blob.name))
            if ext == "webp":
                continue

            msg = {
                "database_name": db_name,
                "customer_table_name": photosapp.CUSTOMERTABLE,
                "top_level_collection_name": photosapp.IMAGESTABLE,
                "bucket_name": customer_rec["bucket_name"],
                "blob_name": blob.name,
                "user_id": customer_rec["uuid"],
            }

            message_id = pubsub_helper.publish_message(topic_name, msg)
            print(f"\n\nPublished message {message_id}.")
            print(json.dumps(msg))
            total_num_msgs_sent += 1
            time.sleep(1)

            if total_num_msgs_sent % msg_batch_size == 0:
                print("\n\nSleeping for 2 seconds...")
                print(f"Total messages sent: {total_num_msgs_sent}, {msg_batch_size}")
                time.sleep(2)

        if maxmessages and total_num_msgs_sent >= maxmessages:
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--maxmessages",
        required=False,
        type=int,
        default=None,
        help="maximum number of messages to send",
    )
    parser.add_argument(
        "--configfile",
        required=True,
        type=Path,
        help="path to the yaml config file",
    )
    parser.add_argument(
        "--email",
        required=True,
        type=str,
        default=None,
        help="customer email to ingest data for",
    )
    parser.add_argument(
        "--testmode",
        required=False,
        action="store_true",
        help="use the test database",
    )

    args = parser.parse_args()
    ingest_data(args.configfile, args.email, args.maxmessages, args.testmode)
