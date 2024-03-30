import argparse
from pathlib import Path
import sys

sys.path.insert(0, "../src")
import yaml

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import photosapp

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
    customer = photosapp.Customer(args.name, args.email, args.phone, args.bucket)

    try:
        db_helper = photosapp.DatabaseHelper(args.configfile)
        if db_helper.check_unique_email(customer.email):
            db_helper.insert_customer(customer)
            print(f"Added customer: {customer}")
        else:
            print(f"Customer {customer.email} already exists")

    except Exception as e:
        print(e)
