import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, "../src")
import time
import yaml

from tqdm import tqdm

import photosapp


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

    args = parser.parse_args()
    with open(args.configfile, "r") as file:
        config = yaml.safe_load(file)

    db_helper = photosapp.DatabaseHelper(args.configfile)
    customer = db_helper.get_customer(args.email)

    assert len(customer) == 1
    if customer[0].exists:
        customer_rec = customer[0].to_dict()
        print(customer_rec)
    else:
        print(f"Could not find customer with email {args.email}")
        sys.exit(1)

    storage_helper = photosapp.GCStoragehelper(args.configfile)
    blobs = storage_helper.get_blobs(customer_rec["bucket_name"])

    pubsub_helper = photosapp.PubSubHelper(args.configfile)
    topic_name = config["topics"]["ingest_topic"]["name"]

    msg_batch_size = config["functions"]["ingest_function"]["max_instances"]

    # Iterate through the blobs and create messages for each.
    total_num_msgs_sent = 0
    for blob in tqdm(blobs):

        if "image" in blob.content_type:
            msg = {
                "database_name": config["firestore"]["database_name"],
                "top_level_collection_name": photosapp.IMAGESTABLE,
                "sub_level_collection_name": photosapp.IMAGESUBTABLE,
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

        if args.maxmessages and total_num_msgs_sent >= args.maxmessages:
            break
