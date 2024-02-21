import os
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from PIL import Image
import io

scopes=['https://www.googleapis.com/auth/photoslibrary.readonly']

creds = None

if os.path.exists('_secrets_/token.json'):
    creds = Credentials.from_authorized_user_file('_secrets_/token.json', scopes)
        
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            '_secrets_/client_secret.json', scopes)
        creds = flow.run_local_server()
    print(creds)
    # Save the credentials for the next run
    with open('_secrets_/token.json', 'w') as token:
        token.write(creds.to_json())


from google.auth.transport.requests import AuthorizedSession
authed_session = AuthorizedSession(creds)

nextPageToken = None
idx = 0
media_items = []
while True:
    idx += 1
    print(idx)
    
    response = authed_session.post(
        'https://photoslibrary.googleapis.com/v1/mediaItems:search', 
        headers = { 'content-type': 'application/json' },
        json={ 
            "pageSize": 100,
            "pageToken": nextPageToken,
            "filters": {
                "dateFilter": {
                    "ranges": [{ 
                        "startDate": {
                            "year": 1980,
                            "month": 1,
                            "day": 1,
                        },
                        "endDate": {
                            "year": 2024,
                            "month": 3,
                            "day": 1,
                        }
                    }]
                }
            }
        })
    
    if idx == 5:
        break
    
    response_json = response.json()
    media_items += response_json["mediaItems"]
    
    if not "nextPageToken" in response_json:
        break
        
    nextPageToken = response_json["nextPageToken"]

photos_df = pd.DataFrame(media_items)
photos_df = pd.concat([photos_df, pd.json_normalize(photos_df.mediaMetadata).rename(columns={"creationTime": "creationTime_metadata"})], axis=1)
#photos_df["creationTime_metadata_dt"] = photos_df.creationTime_metadata.astype("datetime64[ns]")
photos_df["creationTime_metadata_dt"] = pd.to_datetime(photos_df.creationTime_metadata)
print(photos_df.head())

print(photos_df.columns)
print(photos_df.loc[0, :])

image_data_response = authed_session.get(photos_df.baseUrl[1])

image = Image.open(io.BytesIO(image_data_response.content))
image.show()