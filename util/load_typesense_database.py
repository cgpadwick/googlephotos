import argparse
from dotenv import load_dotenv
import os
from pathlib import Path
import sys

sys.path.insert(0, "../src")

from tqdm import tqdm
import yaml

import photosapp
import typesense


def load_typesense_db(config_file, email, maxrecords, test_mode=False):
    """
    Load the Typesense database using data from the Firestore database.

    Parameters:
    - config_file: str, the path to the configuration file
    - email: str, the email address of the customer
    - maxrecords: int, the maximum number of records to load
    - test_mode: bool, optional, whether to run in test mode (default is False)
    """

    load_dotenv()

    with open(config_file, "r") as file:
        config = yaml.safe_load(file)

    db_helper = photosapp.DatabaseHelper(config_file, test_mode)
    customer_rec = db_helper.get_customer(email)

    # Iterate through the documents in the database and generate messages
    # for each one.
    col_ref = (
        db_helper.get_db()
        .collection(f'customers/{customer_rec["uuid"]}/{photosapp.IMAGESTABLE}')
        .order_by("acquisition_time")
    )
    image_list = col_ref.stream()

    # Loop over the images first, creating messages to send.  It turns out that
    # if you leave the firestore connection open too long, it dies.
    print("Retrieving records from Firestore...\n\n")
    record_list = []
    total_num_records = 0
    for img in tqdm(image_list):  # image_list:
        img_caption = img.to_dict().get("caption", None)
        if img_caption is not None:
            img_rec = img.to_dict()
            typesense_rec = {
                "acquisition_time": img_rec["acquisition_time"],
                "bucket_name": img_rec["bucket_name"],
                "blob_name": img_rec["blob_name"],
                "caption": img_rec["caption"],
                "uuid": img_rec["uuid"],
            }
            record_list.append(typesense_rec)
            total_num_records += 1

            if maxrecords and total_num_records >= maxrecords:
                break

    # Now load the typesense DB.
    print("Initializing Typesense Collection...\n\n")
    client = typesense.Client(
        {
            "api_key": os.getenv("TYPESENSE_SEARCH_API_KEY"),
            "nodes": [
                {
                    "host": os.getenv("TYPESENSE_HOST"),
                    "port": "443",
                    "protocol": "https",
                }
            ],
            "connection_timeout_seconds": 10,
        }
    )

    # Clear the images collection.
    client.collections["images"].delete()

    # Set up the schema.
    create_response = client.collections.create(
        {
            "name": "images",
            "fields": [
                {"name": "acquisition_time", "type": "auto"},
                {"name": "blob_name", "type": "string", "facet": True},
                {"name": "bucket_name", "type": "string", "facet": True},
                {"name": "caption", "type": "string", "facet": True, "sort": True},
            ],
            "default_sorting_field": "caption",
        }
    )
    print(create_response)

    print("Loading records...\n\n")
    for rec in tqdm(record_list):
        client.collections["images"].documents.upsert(rec)
    print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--maxrecords",
        required=False,
        type=int,
        default=None,
        help="maximum number of records to load",
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
    load_typesense_db(args.configfile, args.email, args.maxrecords, args.testmode)
