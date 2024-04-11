import os
from flask import Flask, render_template, redirect, url_for, request, session
from flask_session import Session
import textwrap

from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.transport.requests import AuthorizedSession

import visionmodel

app = Flask(__name__)

SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)


# Redirect URI for Google OAuth2
REDIRECT_URI = 'http://localhost:5000/oauth2callback'

# Google Photos API endpoints
API_BASE = 'https://photoslibrary.googleapis.com/v1'
MEDIA_ITEMS_URL = f'{API_BASE}/mediaItems'

# OAuth2 Scope for Google Photos
SCOPE = 'https://www.googleapis.com/auth/photoslibrary.readonly'

# Global variable to store access token
access_token = None


def format_caption(caption):
    """
    Line wraps the caption.

    Args:
        caption: A string representing the caption.

    Returns:
        A string representing the formatted caption.
    """

    wrapped = textwrap.wrap(caption, width=200)
    return "\n".join(wrapped)

def build_date_range(start_date, end_date):

    start_date = start_date.split('-')
    end_date = end_date.split('-')

    start_date = {
        'year': int(start_date[0]),
        'month': int(start_date[1]),
        'day': int(start_date[2])
    }

    end_date = {
        'year': int(end_date[0]),
        'month': int(end_date[1]),
        'day': int(end_date[2])
    }

    return {
        'startDate': start_date,
        'endDate': end_date
    }

@app.route('/')
def index():

    options = ['huggingface', 'openai', 'gemini']
    return render_template('index.html', options=options)

@app.route('/process_date', methods=['POST'])
def process_date():
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    date_range = build_date_range(start_date, end_date)
    session['caption_engine'] = request.form['selected_option']
    print(session['caption_engine'])
 
    try:
        photos = get_photos(date_range)
        session['photos'] = photos
        return render_template('photos.html', photos=photos)
    except Exception as e:
        return render_template('error.html', message=str(e))


def get_auth_session():
    """
    Returns an authorized session for accessing the Google Photos Library API.
    """

    scopes = [SCOPE]
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


def retrieve_media_items(authed_session, date_range, maxpages=None):
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

        response = authed_session.post(
            "https://photoslibrary.googleapis.com/v1/mediaItems:search",
            headers={"content-type": "application/json"},
            json={
                "pageSize": 100,
                "pageToken": nextPageToken,
                "filters": {
                    "dateFilter": {
                        "ranges": [
                            date_range
                        ]
                    }
                },
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

    return media_items


def get_photos(date_range):

    #import pdb; pdb.set_trace()
    authed_session = get_auth_session()
    photos = retrieve_media_items(authed_session, date_range, maxpages=1)

    return photos


def search_for_photos(photos, ids):

    results = []
    for photo in photos:
        if photo['id'] in ids:
            results.append(photo)

    return results

@app.route('/get_captions', methods=['POST'])
def get_captions():

    selected_photos = request.form.getlist('selected_photos')
    session['selected_photos'] = search_for_photos(session['photos'], selected_photos)

    factory = visionmodel.VisionModelFactory()
    model = factory.create(model_str=session['caption_engine'], device='gpu')
    
    for photo in session['selected_photos']:
            caption = model.predict([photo['baseUrl']])
            photo['caption'] = format_caption(caption[0])

    return render_template('photos_with_captions.html', photos=session['selected_photos'])

if __name__ == '__main__':
    app.run(debug=True)
