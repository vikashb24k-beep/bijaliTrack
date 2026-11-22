from __future__ import annotations

import base64
import html
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger("bijlitrack.gmail")

BASE_DIR = Path(__file__).resolve().parents[2]
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailService:
    """Production-grade Gmail API client for extracting SBPDCL electricity receipts."""

    def __init__(
        self,
        credentials_path: Optional[str | Path] = None,
        token_path: Optional[str | Path] = None,
        scopes: Optional[List[str]] = None,
    ) -> None:
        self.credentials_path = Path(credentials_path or CREDENTIALS_FILE)
        self.token_path = Path(token_path or TOKEN_FILE)
        self.scopes = scopes or SCOPES
        self._last_auth_error: Optional[str] = None

    @property
    def credentials_exist(self) -> bool:
        return self.credentials_path.exists()

    @property
    def token_exists(self) -> bool:
        return self.token_path.exists()

    def get_auth_status(self) -> Dict[str, Any]:
        """Check if Gmail credentials and token are valid and refreshable."""
        if not self.token_exists:
            return {
                "connected": False,
                "status": "Token not found. Please connect your Gmail account.",
                "credentials_found": self.credentials_exist,
                "error": self._last_auth_error,
            }

        creds = self._load_credentials()
        if creds and creds.valid:
            return {
                "connected": True,
                "status": "Connected to Gmail (OAuth active)",
                "credentials_found": self.credentials_exist,
                "scopes": self.scopes,
                "error": None,
            }
        elif creds and creds.expired:
            return {
                "connected": False,
                "status": "Gmail token expired or revoked. Re-authorization required.",
                "credentials_found": self.credentials_exist,
                "error": self._last_auth_error or "Token expired or revoked",
            }
        else:
            return {
                "connected": False,
                "status": "Authentication required.",
                "credentials_found": self.credentials_exist,
                "error": self._last_auth_error,
            }

    def _save_credentials(self, credentials: Credentials) -> None:
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(credentials.to_json(), encoding="utf-8")

    def _load_credentials(self) -> Optional[Credentials]:
        if not self.token_path.exists():
            return None

        try:
            with open(self.token_path, "r", encoding="utf-8") as token_file:
                token_data = json.load(token_file)
        except (json.JSONDecodeError, OSError) as exc:
            self._last_auth_error = f"Corrupted token.json: {exc}"
            return None

        try:
            creds = Credentials.from_authorized_user_info(token_data, self.scopes)
        except Exception as exc:
            self._last_auth_error = f"Invalid token format: {exc}"
            return None

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_credentials(creds)
                self._last_auth_error = None
            except Exception as exc:
                self._last_auth_error = f"Failed to refresh token: {exc}"
                return None
        return creds

    def generate_authorization_url(self, redirect_uri: str) -> Tuple[str, str, str]:
        """Generate Google OAuth2 consent URL with PKCE verifier."""
        if not self.credentials_path.exists():
            raise FileNotFoundError(f"Missing {self.credentials_path}")

        flow = Flow.from_client_secrets_file(
            str(self.credentials_path),
            scopes=self.scopes,
            redirect_uri=redirect_uri,
        )
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        code_verifier = getattr(flow, "code_verifier", "")
        return auth_url, state, code_verifier

    def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: str,
        code_verifier: Optional[str] = None,
        state: Optional[str] = None,
    ) -> Credentials:
        """Exchange the OAuth authorization code for tokens and save to token.json."""
        if not self.credentials_path.exists():
            raise FileNotFoundError(f"Missing {self.credentials_path}")

        flow = Flow.from_client_secrets_file(
            str(self.credentials_path),
            scopes=self.scopes,
            redirect_uri=redirect_uri,
            state=state,
        )
        if code_verifier:
            flow.code_verifier = code_verifier

        flow.fetch_token(code=code)
        creds = flow.credentials
        self._save_credentials(creds)
        self._last_auth_error = None
        return creds

    def build_service(self):
        creds = self._load_credentials()
        if not creds or not creds.valid:
            error_msg = self._last_auth_error or "Gmail credentials invalid or expired"
            raise RuntimeError(f"Gmail not authenticated: {error_msg}")
        return build("gmail", "v1", credentials=creds, cache_discovery=False)

    def search_electricity_messages(self, max_results: int = 500) -> List[Dict[str, Any]]:
        """Search Gmail thoroughly with pagination for all SBPDCL PhonePe electricity payments."""
        service = self.build_service()

        # Comprehensive query covering all variations of PhonePe and SBPDCL receipts
        # Over the past 2 years (newer_than:2y)
        queries = [
            (
                'newer_than:2y '
                '("PhonePe" OR from:phonepe.com OR phonepe) '
                '(SBPDCL OR "South Bihar Power" OR "South Bihar" OR "Bihar Bijli" OR "BSPHCL" OR "Sugam" OR "RAPDRP" OR electricity OR "power distribution" OR "smart meter" OR bijli)'
            ),
            (
                'newer_than:2y '
                '("SBPDCL" OR "South Bihar Power Distribution" OR "Bihar Bijli Smart Meter")'
            ),
        ]

        combined_messages_dict: Dict[str, Dict[str, Any]] = {}

        for query in queries:
            page_token = None
            retrieved_for_query = 0

            while retrieved_for_query < max_results:
                try:
                    response = service.users().messages().list(
                        userId="me",
                        q=query,
                        maxResults=min(100, max_results - retrieved_for_query),
                        pageToken=page_token,
                    ).execute()

                    batch = response.get("messages", [])
                    for msg in batch:
                        combined_messages_dict[msg["id"]] = msg

                    retrieved_for_query += len(batch)
                    page_token = response.get("nextPageToken")
                    if not page_token or not batch:
                        break
                except HttpError as exc:
                    logger.error("Gmail search error for query '%s': %s", query, exc)
                    break

        logger.info("Found %d candidate electricity email references in Gmail.", len(combined_messages_dict))
        return list(combined_messages_dict.values())

    def _extract_body_text(self, payload: Dict[str, Any]) -> str:
        """Recursively extract plain text and HTML body, stripping tags and normalizing."""
        body_text = ""
        mime_type = payload.get("mimeType", "")
        body = payload.get("body", {})
        data = body.get("data")

        if data:
            try:
                raw_bytes = base64.urlsafe_b64decode(data.encode("utf-8"))
                decoded = raw_bytes.decode("utf-8", errors="replace")

                # If HTML, clean tags while preserving structure
                if "html" in mime_type.lower() or "<html" in decoded.lower() or "<td" in decoded.lower():
                    # Unescape HTML entities (e.g. &#8377; for ₹, &nbsp;)
                    decoded = html.unescape(decoded)
                    # Replace line-breaking elements with space
                    decoded = re.sub(r"<(?:br|p|div|tr|th|td)[^>]*>", " ", decoded, flags=re.IGNORECASE)
                    # Strip remaining tags
                    clean_text = re.sub(r"<[^>]+>", " ", decoded)
                    body_text += " " + clean_text
                else:
                    body_text += " " + decoded
            except Exception:
                pass

        parts = payload.get("parts", [])
        for part in parts:
            body_text += " " + self._extract_body_text(part)

        # Normalize whitespace
        return re.sub(r"\s+", " ", body_text).strip()

    def get_message_full_details(self, message_id: str) -> Dict[str, Any]:
        """Fetch full metadata and decoded snippet/body for an email message."""
        service = self.build_service()
        msg = service.users().messages().get(
            userId="me",
            id=message_id,
            format="full",
        ).execute()

        payload = msg.get("payload", {})
        headers = payload.get("headers", [])
        header_map: Dict[str, str] = {}
        for h in headers:
            header_map[str(h.get("name", "")).lower()] = str(h.get("value", ""))

        body_text = self._extract_body_text(payload)
        snippet = html.unescape(msg.get("snippet", ""))

        return {
            "id": msg.get("id"),
            "thread_id": msg.get("threadId"),
            "snippet": snippet,
            "body": body_text[:6000],  # increased limit for complete detail inspection
            "from": header_map.get("from", ""),
            "to": header_map.get("to", ""),
            "subject": header_map.get("subject", ""),
            "date": header_map.get("date", ""),
            "message_id": header_map.get("message-id", msg.get("id")),
        }


# Compatibility wrappers
def authenticate_gmail(credentials_path: Optional[str | Path] = None, token_path: Optional[str | Path] = None):
    return GmailService(credentials_path=credentials_path, token_path=token_path).build_service()


def search_emails(service, query: str, max_results: int = 50):
    response = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    return response.get("messages", [])


def get_email_details(service, message_id: str):
    return GmailService().get_message_full_details(message_id)


def find_electricity_emails(service):
    messages = search_emails(
        service,
        'newer_than:2y (from:phonepe OR "PhonePe") (SBPDCL OR "South Bihar Power" OR "electricity" OR "bijli")',
        max_results=100,
    )
    results = []
    for item in messages:
        try:
            results.append(get_email_details(service, item["id"]))
        except Exception:
            continue
    return results
