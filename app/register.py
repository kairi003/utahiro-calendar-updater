import datetime as dt
import os
import os.path
import sys
from logging import basicConfig, getLogger
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CALENDAR_ID = os.environ["CALENDAR_ID"]
EVENT_TITLE = os.environ["EVENT_TITLE"]

USER_TOKEN = "token.json"
CLIENT_SECRET = "credentials.json"

SCOPES = ["https://www.googleapis.com/auth/calendar.events.owned"]


def get_creds() -> Credentials:
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(USER_TOKEN):
        creds = Credentials.from_authorized_user_file(USER_TOKEN, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET, SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(USER_TOKEN, "w") as token:
            token.write(creds.to_json())
    return creds


def register_event(event_date: dt.date) -> Any:
    creds = get_creds()
    service = build("calendar", "v3", credentials=creds)
    data = {
        "summary": EVENT_TITLE,
        "start": {"date": event_date.isoformat()},
        "end": {"date": event_date.isoformat()},
    }
    event = service.events().insert(calendarId=CALENDAR_ID, body=data).execute()
    return event


if __name__ == "__main__":
    get_creds()
