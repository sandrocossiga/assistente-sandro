from fastapi import FastAPI
from pydantic import BaseModel
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

app = FastAPI()

SCOPES = ['https://www.googleapis.com/auth/calendar']

class EventData(BaseModel):
    title: str
    description: str
    start_datetime: str
    end_datetime: str

@app.post("/create_event")
async def create_event(event: EventData):
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    event_body = {
        'summary': event.title,
        'description': event.description,
        'start': {
            'dateTime': event.start_datetime,
            'timeZone': 'Europe/Rome',
        },
        'end': {
            'dateTime': event.end_datetime,
            'timeZone': 'Europe/Rome',
        },
    }

    created_event = service.events().insert(calendarId='primary', body=event_body).execute()
    return {"status": "Evento creato", "link": created_event.get('htmlLink')}