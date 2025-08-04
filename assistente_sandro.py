from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import base64
from datetime import datetime, timedelta

app = FastAPI()

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/tasks'
]

def get_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

class EventData(BaseModel):
    title: str
    description: str
    start_datetime: str
    end_datetime: str

@app.post("/create_event")
async def create_event(event: EventData):
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    body = {
        'summary': event.title,
        'description': event.description,
        'start': {'dateTime': event.start_datetime, 'timeZone': 'Europe/Rome'},
        'end': {'dateTime': event.end_datetime, 'timeZone': 'Europe/Rome'}
    }
    created = service.events().insert(calendarId='primary', body=body).execute()
    return {"status": "Evento creato", "link": created.get('htmlLink')}

class EmailData(BaseModel):
    to: str
    subject: str
    body: str

@app.post("/send_email")
async def send_email(email: EmailData):
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)

    # Costruzione corretta del messaggio
    message_text = (
        f"From: me\r\n"
        f"To: {email.to}\r\n"
        f"Subject: {email.subject}\r\n"
        "\r\n"
        f"{email.body}"
    )
    raw_message = base64.urlsafe_b64encode(message_text.encode()).decode()
    body = {'raw': raw_message}

    sent = service.users().messages().send(userId='me', body=body).execute()
    return {"status": "Email inviata", "id": sent.get('id')}

class DocData(BaseModel):
    title: str
    content: str

@app.post("/create_doc")
async def create_doc(doc: DocData):
    creds = get_credentials()
    service = build('docs', 'v1', credentials=creds)
    document = {"title": doc.title}
    created = service.documents().create(body=document).execute()
    doc_id = created.get('documentId')
    requests_body = [{"insertText": {"location": {"index": 1}, "text": doc.content}}]
    service.documents().batchUpdate(documentId=doc_id, body={"requests": requests_body}).execute()
    return {"status": "Documento creato", "id": doc_id}

class SheetData(BaseModel):
    spreadsheet_id: str
    range: str
    values: list[list[str]]

@app.post("/update_sheet")
async def update_sheet(data: SheetData):
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)
    body = {"values": data.values}
    updated = service.spreadsheets().values().update(
        spreadsheetId=data.spreadsheet_id,
        range=data.range,
        valueInputOption="RAW",
        body=body
    ).execute()
    return {"status": "Sheet aggiornato", "updatedCells": updated.get('updatedCells')}

@app.post("/upload_file")
async def upload_file(file: UploadFile = File(...)):
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)
    file_stream = io.BytesIO(await file.read())
    media = MediaIoBaseUpload(file_stream, mimetype=file.content_type)
    metadata = {'name': file.filename}
    uploaded = service.files().create(body=metadata, media_body=media).execute()
    return {"status": "File caricato", "id": uploaded.get('id')}

class TaskData(BaseModel):
    title: str
    notes: str = None
    due: str = None  # ISO datetime

@app.post("/add_task")
async def add_task(task: TaskData):
    creds = get_credentials()
    service = build('tasks', 'v1', credentials=creds)
    body = {"title": task.title, "notes": task.notes, "due": task.due}
    created = service.tasks().insert(tasklist='@default', body=body).execute()
    return {"status": "Task creato", "id": created.get('id')}

class NoteData(BaseModel):
    text: str

@app.post("/save_note")
async def save_note(note: NoteData):
    creds = get_credentials()
    service = build('keep', 'v1', credentials=creds)
    body = {"title": "Nota da Assistente", "textContent": note.text}
    created = service.notes().create(body=body).execute()
    return {"status": "Nota salvata", "id": created.get('id')}

@app.get("/smart_menu")
async def smart_menu():
    return {
        "actions": [
            "create_event",
            "send_email",
            "create_doc",
            "update_sheet",
            "upload_file",
            "add_task",
            "save_note"
        ]
    }



