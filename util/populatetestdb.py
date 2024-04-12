import argparse
from pathlib import Path
import sys

sys.path.insert(0, "../src")
import yaml

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import photosapp

from ingest_customer_data import ingest_data

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

    db_helper = photosapp.DatabaseHelper(args.configfile, test_mode=True)

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
    ingest_data(args.configfile, customer.email, maxmessages=10, test_mode=True)
