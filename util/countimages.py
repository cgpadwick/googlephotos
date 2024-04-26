import argparse
import yaml

from pathlib import Path

from google.oauth2 import service_account
from google.cloud import storage

from tqdm import tqdm

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--configfile",
        required=True,
        type=Path,
        help="path to the yaml config file",
    )
    parser.add_argument(
        "--bucket",
        required=True,
        type=str,
        help="name of the bucket to count images in",
    )
    parser.add_argument(
        "--print",
        required=False,
        action="store_true",
        help="print the blob names found for each blob in the bucket",
    )

    args = parser.parse_args()
    with open(args.configfile, "r") as file:
        config = yaml.safe_load(file)

    # Get the contents of the bucket.
    creds_path = config["accounts"]["service_account"]["path_to_credentials"]
    source_credentials = service_account.Credentials.from_service_account_file(
        creds_path
    )
    storage_client = storage.Client(credentials=source_credentials)
    bucket = storage_client.get_bucket(args.bucket)
    blobs = bucket.list_blobs()

    # Iterate through the blobs and count the number of images.
    num_images = 0
    for blob in tqdm(blobs):

        if "image" in blob.content_type:
            if args.print:
                print(blob.name)
            num_images += 1

    print(f"\n\nNumber of images found in bucket: {num_images}\n\n")
