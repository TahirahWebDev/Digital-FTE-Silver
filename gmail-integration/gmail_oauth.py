#!/usr/bin/env python3
"""
Gmail OAuth2 Token Generator

Run this script ONCE to authenticate with Gmail API.
It will open a browser window for you to grant permissions.
After authentication, the token is saved to .gmail_token.json
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if required packages are available
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError as e:
    print(f"ERROR: Missing required packages.")
    print(f"Run: pip install -r requirements.txt")
    print(f"Details: {e}")
    sys.exit(1)

# Configuration
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose'
]

CLIENT_ID = os.getenv('GMAIL_CLIENT_ID', '')
CLIENT_SECRET = os.getenv('GMAIL_CLIENT_SECRET', '')
REDIRECT_URI = os.getenv('GMAIL_REDIRECT_URI', 'http://localhost:8080/callback')

TOKEN_FILE = Path(__file__).parent / '.gmail_token.json'
CREDENTIALS_FILE = Path(__file__).parent / 'credentials.json'


def main():
    """Run OAuth2 flow to get Gmail API credentials."""
    print("=" * 60)
    print("Gmail OAuth2 Token Generator")
    print("=" * 60)
    print()
    
    # Check if credentials file exists
    if not CREDENTIALS_FILE.exists():
        print("ERROR: credentials.json not found!")
        print()
        print("To get credentials.json:")
        print("1. Go to: https://console.cloud.google.com/apis/credentials")
        print("2. Create a new project or select existing")
        print("3. Enable Gmail API")
        print("4. Create OAuth2 Client ID (Desktop app)")
        print("5. Download the JSON file")
        print("6. Save it as: credentials.json in the same folder as this script")
        print()
        sys.exit(1)
    
    # Check if token already exists
    if TOKEN_FILE.exists():
        print(f"Token file already exists: {TOKEN_FILE}")
        response = input("Do you want to refresh the token? (y/n): ")
        if response.lower() != 'y':
            print("Using existing token.")
            sys.exit(0)
        TOKEN_FILE.unlink()
        print("Old token deleted.")
        print()
    
    # Verify environment variables
    if not CLIENT_ID or not CLIENT_SECRET:
        print("WARNING: GMAIL_CLIENT_ID or GMAIL_CLIENT_SECRET not set in .env")
        print("Using credentials from credentials.json instead.")
        print()
    
    try:
        print("Starting OAuth2 flow...")
        print("A browser window will open for you to grant permissions.")
        print()
        
        # Create flow
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            SCOPES
        )
        
        # Run local server flow
        creds = flow.run_local_server(
            port=8080,
            bind_addr='127.0.0.1',
            authorization_prompt_message='Opening browser... ',
            success_message='Success! You can close this window.',
            open_browser=True
        )
        
        # Save token
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
        
        print()
        print("=" * 60)
        print("SUCCESS! Token saved to:", TOKEN_FILE)
        print("=" * 60)
        print()
        print("You can now run the Gmail Watcher:")
        print("  python gmail_watcher.py")
        print()
        print("Or start it in background:")
        print("  wscript.exe start_gmail_watcher_hidden.vbs")
        print()
        
    except Exception as e:
        print()
        print("=" * 60)
        print("ERROR: Authentication failed")
        print("=" * 60)
        print(f"Details: {e}")
        print()
        print("Troubleshooting:")
        print("1. Make sure credentials.json is valid")
        print("2. Check that Gmail API is enabled in Google Cloud Console")
        print("3. Try deleting .gmail_token.json and run again")
        print()
        sys.exit(1)


if __name__ == '__main__':
    main()
