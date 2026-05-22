"""
Gmail API client.
Handles OAuth 2.0 authentication, reading and sending emails.
"""
import base64
import email as email_lib
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os


SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
]


def get_gmail_service(credentials_path: str, token_path: str):
    """Authenticate via OAuth 2.0 and return Gmail API service instance."""
    creds = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def fetch_unread_emails(service, max_results: int = 10) -> list[dict]:
    """Fetch unread emails from inbox. Returns list of parsed email dicts."""
    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX", "UNREAD"],
        maxResults=max_results,
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg_ref in messages:
        msg = service.users().messages().get(
            userId="me",
            id=msg_ref["id"],
            format="full",
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        body = _extract_body(msg["payload"])

        emails.append({
            "id": msg["id"],
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", "(no subject)"),
            "body": body,
            "thread_id": msg["threadId"],
        })

    return emails


def send_reply(service, original: dict, reply_body: str):
    """Send a reply to the original email thread."""
    message = MIMEText(reply_body)
    message["To"] = original["from"]
    message["Subject"] = f"Re: {original['subject']}"
    message["In-Reply-To"] = original["id"]
    message["References"] = original["id"]

    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": encoded, "threadId": original["thread_id"]},
    ).execute()


def apply_label(service, message_id: str, label_name: str):
    """Create label if it doesn't exist, then apply it and mark as read."""
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    label_id = next((l["id"] for l in labels if l["name"] == label_name), None)

    if not label_id:
        label = service.users().labels().create(
            userId="me",
            body={"name": label_name},
        ).execute()
        label_id = label["id"]

    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={
            "addLabelIds": [label_id],
            "removeLabelIds": ["UNREAD"],
        },
    ).execute()


def _extract_body(payload: dict) -> str:
    """Recursively extract plain text body from email payload."""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    for part in payload.get("parts", []):
        result = _extract_body(part)
        if result:
            return result

    return ""