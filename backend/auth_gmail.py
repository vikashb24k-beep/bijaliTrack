from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def main():
    print("=" * 60)
    print("BijliTrack - Gmail OAuth2 Re-authentication")
    print("=" * 60)
    print("A browser window will open shortly to connect your Gmail account.")
    print("Please select your Google account and grant read-only Gmail access.\n")

    if not CREDENTIALS_FILE.exists():
        print(f"Error: {CREDENTIALS_FILE} not found!")
        return

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")

    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    print("\n" + "=" * 60)
    print("SUCCESS: Gmail authenticated successfully!")
    print(f"Saved fresh token to: {TOKEN_FILE}")
    print("You can now click 'Sync Now' in BijliTrack to fetch your current bills.")
    print("=" * 60)


if __name__ == "__main__":
    main()
