import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, "../src")
import time
import yaml

from tqdm import tqdm

import photosapp


def ingest_failed_data(config_file, email, logfile, test_mode=False):
    """
    Ingests failed data from a logfile and publishes messages to a topic.

    Args:
        config_file (str): Path to the YAML config file.
        email (str): Email of the customer.
        logfile (str): Path to the logfile containing failed messages.
        test_mode (bool, optional): If True, uses test database. Defaults to False.

    Returns:
        None
    """

    with open(config_file, "r") as file:
        config = yaml.safe_load(file)

    with open(logfile, "r") as f:
        failed_messages = json.load(f)

    db_helper = photosapp.DatabaseHelper(config_file, test_mode)
    customer_rec = db_helper.get_customer(email)

    pubsub_helper = photosapp.PubSubHelper(config_file)
    topic_name = config["topics"]["ingest_topic"]["name"]

    msg_batch_size = config["functions"]["ingest_function"]["max_instances"]

    db_name = config["firestore"]["database_name"]
    if test_mode:
        db_name = config["firestore"]["testdb_name"]

    # Iterate through the failed messages and create ingest messages for each one,
    # publishing them to the topic.
    total_num_msgs_sent = 0
    for entry in failed_messages:

        msg = {
            "database_name": db_name,
            "customer_table_name": photosapp.CUSTOMERTABLE,
            "top_level_collection_name": photosapp.IMAGESTABLE,
            "bucket_name": entry["jsonPayload"]["bucket_name"],
            "blob_name": entry["jsonPayload"]["blob_name"],
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
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
        "--logfile",
        required=True,
        type=Path,
        help="log file containing the failed ingest messages, downloaded from log explorer",
    )
    parser.add_argument(
        "--testmode",
        required=False,
        action="store_true",
        help="use the test database",
    )

    args = parser.parse_args()
    ingest_failed_data(args.configfile, args.email, args.logfile, args.testmode)
