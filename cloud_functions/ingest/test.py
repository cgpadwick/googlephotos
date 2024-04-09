import base64
import json
import main

msg = {"database_name": "photos",
       "customer_table_name": "customers",
       "top_level_collection_name": "testing",
       "bucket_name": "cgp-photos-export", 
       "blob_name": "Google Photos/1987 Porsche Carrera Cabriolet/20201128_101308.jpg", 
       "user_id": "ea36dcd1-8061-4f76-95d7-889004797275"}


event = {"data": base64.b64encode(json.dumps(msg).encode("utf-8"))}

main.ingest_object(event, None)




