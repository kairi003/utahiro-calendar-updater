import datetime as dt
import os
import os.path
import sys
from logging import basicConfig, getLogger
from typing import Any

from google.auth import load_credentials_from_file
from google.auth.credentials import TokenState
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CALENDAR_ID = os.environ["CALENDAR_ID"]
EVENT_TITLE = os.environ["EVENT_TITLE"]

USER_TOKEN = "token.json"
CLIENT_SECRET = "credentials.json"

SCOPES = ["https://www.googleapis.com/auth/calendar.events.owned"]


def get_credentials() -> Credentials:
    """Get the credentials for the Google Calendar API."""

    # For google-github-actions/auth
    if creds_path := os.environ.get("GOOGLE_GHA_CREDS_PATH"):
        creds, project_id = load_credentials_from_file(creds_path, scopes=SCOPES)
        creds.refresh(Request())
        return creds
    
    # For Local Development
    try:
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if creds.token_state is TokenState.FRESH:
            # return the credentials if it is fresh
            return creds
        creds.refresh(Request())
    except (GoogleAuthError, FileNotFoundError):
        # If there are no (valid) credentials available, let the user log in.
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
        token.write(creds.to_json())
    return creds


def register_event(event_date: dt.date) -> Any:
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)
    data = {
        "summary": EVENT_TITLE,
        "start": {"date": event_date.isoformat()},
        "end": {"date": event_date.isoformat()},
    }
    event = service.events().insert(calendarId=CALENDAR_ID, body=data).execute()
    return event

