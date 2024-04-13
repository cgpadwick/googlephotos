import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, "../src")
import time
import yaml

import photosapp


def generate_captions(config_file, email, maxmessages, test_mode=False):
    """
    Generate captions for images based on the provided configuration file.

    Parameters:
    - config_file: str, the path to the configuration file
    - email: str, the email address of the customer
    - maxmessages: int, the maximum number of messages to process
    - test_mode: bool, optional, whether to run in test mode (default is False)
    """

    with open(config_file, "r") as file:
        config = yaml.safe_load(file)

    db_helper = photosapp.DatabaseHelper(config_file, test_mode)
    customer_rec = db_helper.get_customer(email)

    pubsub_helper = photosapp.PubSubHelper(config_file)
    topic_name = config["topics"]["caption_topic"]["name"]

    msg_batch_size = config["functions"]["caption_function"]["max_instances"]

    db_name = config["firestore"]["database_name"]
    if test_mode:
        db_name = config["firestore"]["testdb_name"]

    # Iterate through the documents in the database and generate messages
    # for each one.
    col_ref = db_helper.get_db().collection(
        f'customers/{customer_rec["uuid"]}/{photosapp.IMAGESTABLE}'
    ).order_by('acquisition_time')
    image_list = col_ref.stream()

    # Loop over the images first, creating messages to send.  It turns out that 
    # if you leave the firestore connection open too long, it dies.
    msg_list = []
    total_num_msgs = 0
    for img in image_list:
        # Captioning is expensive, only run it when there is no existing caption.
        img_caption = img.to_dict().get('caption', None)
        if img_caption is None:
            msg = {
                "database_name": db_name,
                "document_path": f'{photosapp.CUSTOMERTABLE}/{customer_rec["uuid"]}/{photosapp.IMAGESTABLE}/{img.id}',
            }
            msg_list.append(msg)
            total_num_msgs += 1

            if maxmessages and total_num_msgs >= maxmessages:
                break

    # Now send the messages in the msg_list, making sure not to overwhelm
    # the cloud functions.
    total_num_msgs_sent = 0
    for msg in msg_list:
        message_id = pubsub_helper.publish_message(topic_name, msg)
        total_num_msgs_sent += 1
        print(f"\n\nPublished message {message_id}.")
        print(json.dumps(msg))
        time.sleep(2)

        if total_num_msgs_sent % msg_batch_size == 0:
            print("\n\nSleeping for 15 seconds...")
            print(f"Total messages sent: {total_num_msgs_sent}, {msg_batch_size}")
            time.sleep(15)

        


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
    generate_captions(args.configfile, args.email, args.maxmessages, args.testmode)
