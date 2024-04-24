import argparse
from pathlib import Path
import sys

sys.path.insert(0, "../src")
import time
import yaml

import photosapp

from ingest_customer_data import ingest_data
from generate_captions import generate_captions


def populate_test_db(config_file, maxmessages=None):

    with open(args.configfile, "r") as file:
        config = yaml.safe_load(file)

    db_helper = photosapp.DatabaseHelper(config_file, True)

    # Start from a clean DB.
    db_helper.clear_firestore_collections()

    # Insert the customer into the test database.
    customer = photosapp.Customer(
        "John Doe",
        "me@email.com",
        "123-456-7891",
        config["buckets"]["test_bucket"]["name"],
    )
    db_helper.insert_customer(customer)

    # Add some data to the customer table.
    print("\n\nIngesting Data into the database...")
    ingest_data(config_file, customer.email, maxmessages=maxmessages, test_mode=True)
    time.sleep(10)
    print("Done. \n\n")

    # Generate captions for the images in the test database.
    print("Generating captions for the images...")
    generate_captions(
        config_file, customer.email, maxmessages=maxmessages, test_mode=True
    )
    print("Done. \n\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--configfile",
        required=True,
        type=Path,
        help="path to the yaml config file",
    )

    args = parser.parse_args()

    populate_test_db(args.configfile, maxmessages=None)
