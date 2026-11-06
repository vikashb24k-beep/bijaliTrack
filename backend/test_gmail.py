from typing import Any

from app.services.gmail_service import authenticate_gmail, find_electricity_emails


def safe_display(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.encode("ascii", "replace").decode("ascii")


def main() -> None:
    print("\nConnecting to Gmail...")

    try:
        service = authenticate_gmail()
    except Exception as exc:
        print(f"Gmail authentication failed: {exc}")
        return

    print("Gmail authentication successful!")
    print("\nSearching for electricity-related emails...")

    try:
        emails = find_electricity_emails(service)
    except Exception as exc:
        print(f"Email search failed: {exc}")
        return

    print(f"\nFound {len(emails)} matching emails.\n")

    if not emails:
        print("No electricity-related Gmail messages matched the current search.")
        print("Gmail integration test completed.")
        return

    for index, email in enumerate(emails, start=1):
        print("=" * 60)
        print(f"Email {index}")
        print("Sender:", safe_display(email.get("from", "")))
        print("Subject:", safe_display(email.get("subject", "")))
        print("Date:", safe_display(email.get("date", "")))
        print("Snippet:", safe_display(email.get("snippet", "")))

    print("\nGmail integration test completed.")


if __name__ == "__main__":
    main()
