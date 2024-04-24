import argparse
from functools import partial
import multiprocessing
from pathlib import Path
import sys

sys.path.insert(0, "../src")
sys.path.insert(0, "../cloud_functions/ingest")
from tqdm import tqdm

import photosapp
from main import generate_webp_image

from google.cloud import storage

def process_record(record):
    """
    Process a record by generating a WebP image.

    Args:
        record (dict): A dictionary containing the bucket name and blob name.

    Returns:
        str: The name of the generated WebP image.

    Raises:
        None
    """
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(record["bucket_name"])
    blob = bucket.get_blob(record["blob_name"])
    webp_name = generate_webp_image(bucket, blob, storage_client)
    return webp_name


def generate_webp_images(config_file, email, test_mode=False):
    """
    Generate WebP images based on the provided configuration file, email, and test mode flag.

    Args:
        config_file (str): The path to the configuration file.
        email (str): The email address of the customer.
        test_mode (bool, optional): Whether to run in test mode. Defaults to False.

    Returns:
        None

    Raises:
        None
    """

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
    rec_list = []
    print("\n\nQuerying the database...\n\n")
    for img in tqdm(image_list):
        doc = img.to_dict()
        rec = {
            "bucket_name": doc["bucket_name"],
            "blob_name": doc["blob_name"],
        }
        rec_list.append(rec)
    print(f"\n\nFound {len(rec_list)} records to process.\n\n")

    # Now process the records, generating webp images for each record
    print("\n\nGenerating WebP images...\n\n")
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    results = []
    for result in tqdm(pool.imap(process_record, rec_list), total=len(rec_list)):
        results.append(result)

    pool.close()
    pool.join()

    print(f"\n\nDone.  Generated {len(list(filter(None, results)))} webp images.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--maxrecords",
        required=False,
        type=int,
        default=None,
        help="maximum number of webp files to generate",
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
    generate_webp_images(args.configfile, args.email, args.testmode)
