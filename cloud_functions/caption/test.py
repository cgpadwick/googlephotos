import base64
from dotenv import load_dotenv
import json
import main
import os
import sys

sys.path.insert(0, "../../src")

import photosapp

load_dotenv()

if not "OPENAI_API_KEY" in os.environ:
    raise Exception("Missing OPENAI_API_KEY in environment")

db_helper = photosapp.DatabaseHelper("../../util/infra.yaml", True)

# Get a customer.
col_ref = db_helper.get_db().collection("customers")
customer_list = col_ref.get()
assert len(customer_list) != 0
customer = customer_list[0].to_dict()

# Get a document.
col_ref = db_helper.db.collection(
    f'customers/{customer["uuid"]}/{photosapp.IMAGESTABLE}'
)
image_list = col_ref.get()
assert len(image_list) != 0
image_id = image_list[0].id

msg = {
    "database_name": "testdb",
    "document_path": f'customers/{customer["uuid"]}/{photosapp.IMAGESTABLE}/{image_id}',
}

event = {"data": base64.b64encode(json.dumps(msg).encode("utf-8"))}
main.caption_image(event, None)
