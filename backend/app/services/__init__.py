
"""Service layer exports for BijliTrack."""

from .gmail_service import (
    GmailService,
    authenticate_gmail,
    find_electricity_emails,
    get_email_details,
    search_emails,
)

__all__ = [
    "GmailService",
    "authenticate_gmail",
    "search_emails",
    "get_email_details",
    "find_electricity_emails",
]
