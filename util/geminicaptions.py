import argparse
import yaml

from pathlib import Path
import sys

sys.path.insert(0, "../src")

from google.oauth2 import service_account
import vertexai
from vertexai.preview.vision_models import Image, ImageTextModel

import photosapp


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--maximages",
        required=False,
        type=int,
        default=None,
        help="maximum number of images to process",
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
        "--numberofresults",
        required=False,
        type=int,
        default=3,
        help="the number of results to return from the model",
    )

    args = parser.parse_args()
    with open(args.configfile, "r") as file:
        config = yaml.safe_load(file)

    # Determine the customer corresponding to the email and the bucket.
    db_helper = photosapp.DatabaseHelper(args.configfile)
    customer = db_helper.get_customer(args.email)

    storage_helper = photosapp.GCStoragehelper(args.configfile)
    bucket = storage_helper.get_bucket(customer["bucket_name"])
    blobs = bucket.list_blobs()

    # Initialize the vertexai stack.
    creds_path = config["accounts"]["service_account"]["path_to_credentials"]
    source_credentials = service_account.Credentials.from_service_account_file(
        creds_path
    )
    vertexai.init(project=config["project_id"], credentials=source_credentials)
    # According to the google model garden, imagetext@001 is the only model available.
    model = ImageTextModel.from_pretrained("imagetext@001")

    # Iterate through the blobs and get captions for each image.
    num_images = 0
    for blob in blobs:

        if "image" in blob.content_type:
            image_bytes = blob.download_as_bytes()
            img = Image(image_bytes=image_bytes)
            captions = model.get_captions(
                image=img, language="en", number_of_results=args.numberofresults
            )
            print(f"{blob.name}")
            print(f"{captions}\n\n")

            if args.maximages is not None and num_images >= args.maximages:
                break
            num_images += 1
