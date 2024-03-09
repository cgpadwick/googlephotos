import argparse
import io
import os

import pandas as pd
from pathlib import Path

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from tqdm import tqdm

from PIL import Image


def get_auth_session():
    """
    Returns an authorized session for accessing the Google Photos Library API.
    """

    scopes = ["https://www.googleapis.com/auth/photoslibrary.readonly"]
    creds = None

    if os.path.exists("_secrets_/token.json"):
        creds = Credentials.from_authorized_user_file("_secrets_/token.json", scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "_secrets_/client_secret.json", scopes
            )
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open("_secrets_/token.json", "w") as token:
            token.write(creds.to_json())

    authed_session = AuthorizedSession(creds)

    return authed_session


def retrieve_media_items(authed_session, maxpages=None):
    """
    Retrieves media items from a Google Photos library using the provided authenticated session.

    Args:
        authed_session: The authenticated session to use for making the API request.
        maxpages (int, optional): The maximum number of pages to retrieve. Defaults to None.

    Returns:
        pandas.DataFrame: A DataFrame containing the retrieved media items with additional metadata.
    """

    nextPageToken = None
    idx = 0
    media_items = []
    while True:
        idx += 1
        print(idx)

        response = authed_session.post(
            "https://photoslibrary.googleapis.com/v1/mediaItems:search",
            headers={"content-type": "application/json"},
            json={
                "pageSize": 100,
                "pageToken": nextPageToken,
            },
        )

        response_json = response.json()
        media_items += response_json["mediaItems"]

        # Check maxpages argument
        if maxpages and idx == maxpages:
            break

        if not "nextPageToken" in response_json:
            break

        nextPageToken = response_json["nextPageToken"]

    photos_df = pd.DataFrame(media_items)
    photos_df = pd.concat(
        [
            photos_df,
            pd.json_normalize(photos_df.mediaMetadata).rename(
                columns={"creationTime": "creationTime_metadata"}
            ),
        ],
        axis=1,
    )
    photos_df["creationTime_metadata_dt"] = pd.to_datetime(
        photos_df.creationTime_metadata
    )

    return photos_df


def download_images(photos_df, outdir):
    """
    Download images based on the provided photo dataframe and save them to the specified output directory.

    Args:
        photos_df: A pandas DataFrame containing information about the photos to be downloaded.
        outdir: A string representing the directory where the images will be saved.

    Returns:
        None
    """

    supported_types = [".jpg", ".jpeg", ".png"]
    for _, row in tqdm(photos_df.iterrows()):
        if Path(row.filename).suffix in supported_types:
            image_data_response = authed_session.get(row.baseUrl)
            image = Image.open(io.BytesIO(image_data_response.content))
            image.save(os.path.join(outdir / Path(f"{row.filename}")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--outdir",
        required=False,
        type=Path,
        help="location where the images will be downloaded",
    )
    parser.add_argument(
        "--save-filename",
        required=True,
        type=Path,
        help="location where the media items json file will be saved",
    )
    parser.add_argument(
        "--maxpages",
        required=False,
        type=int,
        default=None,
        help="max number of pages that will be retrieved from google photos api",
    )
    parser.add_argument(
        "--download",
        required=False,
        action="store_true",
        help="photos will be downloaded from google photos api",
    )

    args = parser.parse_args()

    if args.download:
        if not args.outdir:
            raise ValueError("Must provide --outdir if --download is True")
        else:
            if not args.outdir.exists():
                raise ValueError(f"Invalid path specified: {args.outdir}")

    authed_session = get_auth_session()
    photos_df = retrieve_media_items(authed_session, maxpages=args.maxpages)
    if args.download:
        download_images(photos_df, args.outdir)

    photos_df.to_json(args.save_filename, orient="records", lines=True, indent=4)
