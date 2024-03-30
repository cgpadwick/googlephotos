import argparse
from pathlib import Path
import sys

sys.path.insert(0, "../src")
import yaml

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from photosapp import Customer

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--configfile",
        required=True,
        type=Path,
        help="path to the yaml config file",
    )
    parser.add_argument(
        "--name",
        required=True,
        type=str,
        help="first and last name of the customer",
    )
    parser.add_argument(
        "--email",
        required=True,
        type=str,
        help="the email of the customer",
    )
    parser.add_argument(
        "--phone",
        required=True,
        type=str,
        help="phone number including area code",
    )
    parser.add_argument(
        "--bucket",
        required=True,
        type=str,
        help="bucket associated with customer",
    )

    args = parser.parse_args()
    with open(args.configfile, "r") as file:
        config = yaml.safe_load(file)

    customer = Customer(args.name, args.email, args.phone, args.bucket)

    try:
        # Firestore setup.
        creds_path = config["accounts"]["service_account"]["path_to_credentials"]
        creds = credentials.Certificate(creds_path)
        app = firebase_admin.initialize_app(creds)
        db = firestore.Client(database=config["firestore"]["database_name"])

        doc_ref = db.collection("customers").document(str(customer.uuid))
        doc_ref.set(customer.to_dict())

        print(f"Added customer: {customer}")
    except Exception as e:
        print(e)
