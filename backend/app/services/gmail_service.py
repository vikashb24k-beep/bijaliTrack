
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


BASE_DIR = Path(__file__).resolve().parents[2]
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailService:
    """Wrapper around the Gmail API with OAuth2 support."""

    def __init__(
        self,
        credentials_path: Optional[str | Path] = None,
        token_path: Optional[str | Path] = None,
        scopes: Optional[List[str]] = None,
    ) -> None:
        self.credentials_path = Path(credentials_path or CREDENTIALS_FILE)
        self.token_path = Path(token_path or TOKEN_FILE)
        self.scopes = scopes or SCOPES

    def _save_credentials(self, credentials: Credentials) -> None:
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(credentials.to_json(), encoding="utf-8")

    def _load_credentials(self) -> Optional[Credentials]:
        if not self.token_path.exists():
            return None

        try:
            with open(self.token_path, "r", encoding="utf-8") as token_file:
                token_data = json.load(token_file)
        except (json.JSONDecodeError, OSError):
            return None

        creds = Credentials.from_authorized_user_info(token_data, self.scopes)
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_credentials(creds)
            except Exception:
                return None
        return creds

    def authenticate(self):
        creds = self._load_credentials()

        if creds and creds.valid:
            return creds

        if not self.credentials_path.exists():
            raise FileNotFoundError(f"Gmail credentials not found: {self.credentials_path}")

        flow = InstalledAppFlow.from_client_secrets_file(
            str(self.credentials_path),
            self.scopes,
        )
        creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
        self._save_credentials(creds)
        return creds

    def build_service(self):
        return build("gmail", "v1", credentials=self.authenticate(), cache_discovery=False)

    def search_messages(self, query: str, max_results: int = 30) -> List[Dict[str, Any]]:
        service = self.build_service()
        response = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
        return response.get("messages", [])

    def get_message_details(self, message_id: str) -> Dict[str, Any]:
        service = self.build_service()
        message = (
            service.users()
            .messages()
            .get(userId="me", id=message_id, format="metadata", metadataHeaders=["From", "Subject", "Date"])
            .execute()
        )

        headers = message.get("payload", {}).get("headers", [])
        details: Dict[str, Any] = {
            "id": message.get("id"),
            "thread_id": message.get("threadId"),
            "snippet": message.get("snippet", ""),
            "from": "",
            "subject": "",
            "date": "",
        }

        for header in headers:
            name = str(header.get("name", "")).lower()
            value = str(header.get("value", ""))
            if name == "from":
                details["from"] = value
            elif name == "subject":
                details["subject"] = value
            elif name == "date":
                details["date"] = value

        return details

    def find_electricity_emails(self) -> List[Dict[str, Any]]:
        """Search Gmail for electricity-related messages and extract their metadata."""
        query_terms = [
            "SBPDCL",
            "\"South Bihar Power Distribution\"",
            "\"Bihar Bijli\"",
            "\"electricity recharge\"",
            "\"smart meter recharge\"",
            "\"electricity bill\"",
            "\"power bill\"",
        ]
        query = "newer_than:2y (" + " OR ".join(query_terms) + ")"
        messages = self.search_messages(query)
        results: List[Dict[str, Any]] = []

        for message in messages:
            try:
                results.append(self.get_message_details(message["id"]))
            except (KeyError, HttpError):
                continue

        return results


def authenticate_gmail(credentials_path: Optional[str | Path] = None, token_path: Optional[str | Path] = None):
    """Compatibility wrapper for the Gmail OAuth service."""
    return GmailService(credentials_path=credentials_path, token_path=token_path).build_service()


def search_emails(service, query: str, max_results: int = 30):
    """Search Gmail by query and return message references."""
    response = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    return response.get("messages", [])


def get_email_details(service, message_id: str):
    """Fetch metadata for a Gmail message."""
    message = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="metadata", metadataHeaders=["From", "Subject", "Date"])
        .execute()
    )

    headers = message.get("payload", {}).get("headers", [])
    details: Dict[str, Any] = {
        "id": message.get("id"),
        "thread_id": message.get("threadId"),
        "snippet": message.get("snippet", ""),
        "from": "",
        "subject": "",
        "date": "",
    }

    for header in headers:
        name = str(header.get("name", "")).lower()
        value = str(header.get("value", ""))
        if name == "from":
            details["from"] = value
        elif name == "subject":
            details["subject"] = value
        elif name == "date":
            details["date"] = value

    return details


def find_electricity_emails(service):
    """Find electricity-related emails matching expected Bihar utility patterns."""
    query_terms = [
        "SBPDCL",
        '"South Bihar Power Distribution"',
        '"Bihar Bijli"',
        '"electricity recharge"',
        '"smart meter recharge"',
        '"electricity bill"',
        '"power bill"',
    ]
    query = "newer_than:2y (" + " OR ".join(query_terms) + ")"
    messages = search_emails(service, query)
    results: List[Dict[str, Any]] = []

    for item in messages:
        try:
            details = get_email_details(service, item["id"])
            results.append(details)
        except (KeyError, HttpError):
            continue

    return results
