import argparse
from functools import partial
import multiprocessing
import os
from pathlib import Path
import sys

sys.path.insert(0, "../src")
from tqdm import tqdm

from google.cloud import firestore_v1

import photosapp


def process_blob_name(blob_name, config_file, test_mode, email):
    """
    Process a blob name by querying the database to check if it exists and if it is unique. If the blob does not exist in the database, None is returned. If the blob exists and is unique, None is returned. If the blob exists and is not unique, the "best" record is found and the others are deleted. The function returns True if the deletion is successful and None otherwise.

    Parameters:
        blob_name (str): The name of the blob to process.
        config_file (Path): The path to the configuration file.
        test_mode (bool): A flag indicating whether the function is running in test mode.
        email (str): The email of the customer.

    Returns:
        None or bool: None if the blob does not exist in the database or if it is unique. True if the deletion is successful and None otherwise.
    """
    try:
        db_helper = photosapp.DatabaseHelper(config_file, test_mode)
        customer = db_helper.get_customer(email)
        field_filter = firestore_v1.base_query.FieldFilter("blob_name", "==", blob_name)
        query = (
            db_helper.get_db()
            .collection(f'customers/{customer["uuid"]}/{photosapp.IMAGESTABLE}')
            .where(filter=field_filter)
        )
        docs = query.get()

        if len(docs) == 0:
            # This blob does not exist in the database.
            return None
        elif len(docs) == 1:
            # This blob exists in the database and is unique.
            return None
        else:
            # This blob exists in the database and is not unique.
            # Find the "best" record and delete the others.
            num_keys_in_records = []
            for doc_ref in docs:
                doc = doc_ref.to_dict()
                num_keys_in_records.append(len(doc.keys()))

            max_idx = num_keys_in_records.index(max(num_keys_in_records))
            for idx, doc_ref in enumerate(docs):
                if idx != max_idx:
                    doc_ref.reference.delete()
            return True

    except Exception as e:
        print(e)
        return None


def dedup_database_records(config_file, email, test_mode=False):

    # Dedup records in the database.
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

    # Loop over the images first, creating records to process.  It turns out that
    # if you leave the firestore connection open too long, it dies.
    print("\n\nQuerying the database...\n\n")
    blob_names_to_process = []
    for img_ref in tqdm(image_list):
        blob_names_to_process.append(img_ref.to_dict()["blob_name"])
    print(f"\n\nFound {len(blob_names_to_process)} UNIQUE blob_names to dedup.\n\n")

    # Make sure that the blob names are unique otherwise we can run into weird
    # race conditions in the threads (e.g two theads trying to dedup the same
    # blob name.)
    blob_names_to_process = list(set(blob_names_to_process))

    print("\n\nDeduping the database...\n\n")
    with multiprocessing.Pool(processes=multiprocessing.cpu_count() // 2) as pool:
        results = list(
            tqdm(
                pool.imap(
                    partial(
                        process_blob_name,
                        config_file=config_file,
                        test_mode=test_mode,
                        email=email,
                    ),
                    blob_names_to_process,
                ),
                total=len(blob_names_to_process),
            )
        )

    print(f"\n\nDone.  Deduped {len(list(filter(None, results)))} records.\n\n")


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
        "--testmode",
        required=False,
        action="store_true",
        help="use the test database",
    )

    args = parser.parse_args()
    dedup_database_records(args.configfile, args.email, args.testmode)
