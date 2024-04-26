import argparse
import yaml

from pathlib import Path
import sys

sys.path.insert(0, "../src")
from tqdm import tqdm

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
        "--email",
        required=True,
        type=str,
        help="the email to check the captions for",
    )
    parser.add_argument(
        "--field",
        required=True,
        type=str,
        help="the field that you want to count, e.g. 'caption'",
    )
    parser.add_argument(
        "--testmode",
        required=False,
        action="store_true",
        help="use the test database",
    )
    args = parser.parse_args()

    db_helper = photosapp.DatabaseHelper(args.configfile, args.testmode)
    customer = db_helper.get_customer(args.email)

    col_ref = db_helper.get_db().collection(
        f'customers/{customer["uuid"]}/{photosapp.IMAGESTABLE}'
    )
    image_list = col_ref.stream()

    total_num_records = 0
    for img in tqdm(image_list):
        field_value = img.to_dict().get(args.field, None)
        if field_value is not None:
            total_num_records += 1

    print(
        f"Number of records found for customer with email {args.email} with field \'{args.field}\' was : {total_num_records}"
    )
