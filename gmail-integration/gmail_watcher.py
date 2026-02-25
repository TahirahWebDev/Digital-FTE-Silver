#!/usr/bin/env python3
"""
Gmail Watcher - Autonomous Email Monitor

Polls Gmail API every 120 seconds for unread, important emails.
Creates markdown files in /Needs_Action for each new email.
Runs 24/7 in background with auto-recovery.

Features:
- OAuth2 authentication with persistent tokens
- Duplicate prevention using state file
- Exponential backoff retry logic
- Rate limiting (max 10 emails/hour)
- DRY_RUN mode for safe testing
- Never crashes on API failure
"""

import os
import sys
import time
import json
import base64
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
from email.parser import Parser

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', 'F:\\Tahirah\\Hackathon-0\\AI_Employee_Vault'))
NEEDS_ACTION_FOLDER = VAULT_PATH / os.getenv('NEEDS_ACTION_FOLDER', '02_Needs_Actions')
LOGS_FOLDER = VAULT_PATH / os.getenv('LOGS_FOLDER', 'Logs')
STATE_FILE = Path(__file__).parent / '.gmail_state.json'
TOKEN_FILE = Path(__file__).parent / '.gmail_token.json'
CREDENTIALS_FILE = Path(__file__).parent / 'credentials.json'

POLL_INTERVAL = int(os.getenv('GMAIL_POLL_INTERVAL', '120'))
MAX_EMAILS_PER_HOUR = int(os.getenv('GMAIL_MAX_EMAILS_PER_HOUR', '10'))
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'
RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'

# Gmail API Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_FOLDER / 'gmail_watcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GmailWatcher:
    """Autonomous Gmail watcher with state management and rate limiting."""
    
    def __init__(self):
        self.service = None
        self.state = self._load_state()
        self.emails_processed_this_hour: List[datetime] = []
        self.last_state_save = datetime.now()
        
        # Ensure folders exist
        NEEDS_ACTION_FOLDER.mkdir(parents=True, exist_ok=True)
        LOGS_FOLDER.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Gmail Watcher initialized (DRY_RUN={DRY_RUN})")
    
    def _load_state(self) -> Dict[str, Any]:
        """Load persistent state from file."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
                    logger.info("Loaded existing state file")
                    return state
            except Exception as e:
                logger.warning(f"Could not load state file: {e}")
        
        return {
            'processed_email_ids': [],
            'last_poll': None,
            'total_emails_processed': 0,
            'last_history_id': None
        }
    
    def _save_state(self):
        """Save state to file."""
        try:
            # Limit processed IDs to last 10000 to prevent file bloat
            if len(self.state['processed_email_ids']) > 10000:
                self.state['processed_email_ids'] = self.state['processed_email_ids'][-10000:]
            
            with open(STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=2)
            
            self.last_state_save = datetime.now()
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def _authenticate(self) -> bool:
        """Authenticate with Gmail API."""
        try:
            creds = None
            
            # Load existing token
            if TOKEN_FILE.exists():
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            
            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Refreshing expired token...")
                    creds.refresh(Request())
                else:
                    logger.error("No valid credentials found. Please run gmail_oauth.py first.")
                    logger.error("Run: python gmail_oauth.py")
                    return False
            
            # Build service
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail API authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        if not RATE_LIMIT_ENABLED:
            return True
        
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # Filter emails processed in last hour
        self.emails_processed_this_hour = [
            ts for ts in self.emails_processed_this_hour 
            if ts > one_hour_ago
        ]
        
        if len(self.emails_processed_this_hour) >= MAX_EMAILS_PER_HOUR:
            logger.warning(f"Rate limit reached ({MAX_EMAILS_PER_HOUR}/hour). Waiting...")
            return False
        
        return True
    
    def _fetch_emails(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """Fetch unread emails from Gmail."""
        if not self.service:
            return []

        try:
            # Query: unread emails (removed is:important to catch all unread)
            query = 'is:unread'

            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                logger.info("No new unread emails")
                return []

            logger.info(f"Found {len(messages)} unread emails")
            
            # Fetch full message details
            emails = []
            for msg in messages:
                if msg['id'] not in self.state['processed_email_ids']:
                    full_message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    emails.append(full_message)
            
            return emails
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return []
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    def _parse_email(self, message: Dict[str, Any]) -> Dict[str, str]:
        """Parse email message into structured data."""
        headers = message['payload']['headers']
        
        email_data = {
            'id': message['id'],
            'from': '',
            'to': '',
            'subject': '',
            'date': '',
            'snippet': message.get('snippet', ''),
            'body': ''
        }
        
        for header in headers:
            name = header['name'].lower()
            value = header['value']
            
            if name == 'from':
                email_data['from'] = value
            elif name == 'to':
                email_data['to'] = value
            elif name == 'subject':
                email_data['subject'] = value
            elif name == 'date':
                email_data['date'] = value
        
        # Extract body
        body = self._extract_body(message['payload'])
        email_data['body'] = body
        
        return email_data
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from payload."""
        body = ''
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        data = part['body']['data']
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
                        break
        elif 'body' in payload:
            if 'data' in payload['body']:
                data = payload['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
        
        return body[:5000]  # Limit body length
    
    def _create_email_file(self, email_data: Dict[str, str]) -> Optional[Path]:
        """Create markdown file for email in Needs_Action folder."""
        try:
            # Sanitize filename
            subject = email_data['subject'][:50]
            subject = re.sub(r'[^\w\s-]', '', subject)
            subject = subject.strip().replace(' ', '_')
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"EMAIL_{email_data['id']}_{subject}_{timestamp}.md"
            filepath = NEEDS_ACTION_FOLDER / filename
            
            # Determine priority
            priority = self._determine_priority(email_data)
            
            # Parse received date
            received = email_data['date']
            
            # Create markdown content
            content = f"""---
type: email
from: {email_data['from']}
to: {email_data['to']}
subject: {email_data['subject']}
received: {received}
priority: {priority}
status: pending
gmail_id: {email_data['id']}
---

# Email: {email_data['subject']}

**From:** {email_data['from']}  
**To:** {email_data['to']}  
**Received:** {received}  
**Priority:** {priority}

---

## Message

{email_data['body']}

---

## Actions Required

- [ ] Review email content
- [ ] Classify intent
- [ ] Draft response (if needed)
- [ ] Take action or archive

---

*Created by Gmail Watcher at {datetime.now().isoformat()}*
*Gmail ID: {email_data['id']}*
"""
            
            if DRY_RUN:
                logger.info(f"[DRY_RUN] Would create: {filepath}")
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Created email file: {filepath}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to create email file: {e}")
            return None
    
    def _determine_priority(self, email_data: Dict[str, str]) -> str:
        """Determine email priority based on content."""
        subject = email_data['subject'].lower()
        from_addr = email_data['from'].lower()
        
        # High priority keywords
        high_priority_keywords = ['urgent', 'asap', 'immediate', 'important', 'deadline', 'action required']
        
        for keyword in high_priority_keywords:
            if keyword in subject:
                return 'high'
        
        # Check if from important sender
        important_domains = ['boss', 'ceo', 'client', 'customer', 'support']
        for domain in important_domains:
            if domain in from_addr:
                return 'high'
        
        # Medium priority keywords
        medium_priority_keywords = ['meeting', 'review', 'approval', 'question', 'update']
        
        for keyword in medium_priority_keywords:
            if keyword in subject:
                return 'medium'
        
        return 'normal'
    
    def _log_action(self, action_type: str, email_data: Dict[str, Any], result: str):
        """Log action to logs folder."""
        try:
            log_file = LOGS_FOLDER / f"gmail_{datetime.now().strftime('%Y-%m-%d')}.json"
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'action_type': action_type,
                'email_id': email_data.get('id', 'unknown'),
                'subject': email_data.get('subject', ''),
                'from': email_data.get('from', ''),
                'result': result,
                'dry_run': DRY_RUN
            }
            
            # Load existing logs
            logs = []
            if log_file.exists():
                try:
                    with open(log_file, 'r') as f:
                        logs = json.load(f)
                except:
                    logs = []
            
            logs.append(log_entry)
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to log action: {e}")
    
    def process_emails(self) -> int:
        """Process new emails. Returns count of emails processed."""
        if not self._check_rate_limit():
            return 0
        
        emails = self._fetch_emails()
        processed_count = 0
        
        for email in emails:
            try:
                email_data = self._parse_email(email)
                
                if DRY_RUN:
                    logger.info(f"[DRY_RUN] Would process email: {email_data['subject']}")
                    processed_count += 1
                    continue
                
                # Create file in Needs_Action
                filepath = self._create_email_file(email_data)
                
                if filepath:
                    # Update state
                    self.state['processed_email_ids'].append(email_data['id'])
                    self.state['total_emails_processed'] += 1
                    self.state['last_poll'] = datetime.now().isoformat()
                    
                    # Track for rate limiting
                    self.emails_processed_this_hour.append(datetime.now())
                    
                    # Log action
                    self._log_action('email_received', email_data, 'file_created')
                    
                    processed_count += 1
                    logger.info(f"Processed email: {email_data['subject']}")
                
            except Exception as e:
                logger.error(f"Error processing email {email.get('id', 'unknown')}: {e}")
                continue
        
        # Save state
        self._save_state()
        
        return processed_count
    
    def run(self):
        """Main run loop. Runs continuously."""
        logger.info("=" * 60)
        logger.info("Gmail Watcher Starting...")
        logger.info(f"Poll Interval: {POLL_INTERVAL} seconds")
        logger.info(f"DRY_RUN: {DRY_RUN}")
        logger.info(f"Max Emails/Hour: {MAX_EMAILS_PER_HOUR}")
        logger.info("=" * 60)
        
        # Authenticate
        if not self._authenticate():
            logger.error("Failed to authenticate. Exiting.")
            return
        
        consecutive_errors = 0
        max_errors = 10
        
        while True:
            try:
                # Process emails
                count = self.process_emails()
                
                if count > 0:
                    logger.info(f"Processed {count} new email(s)")
                
                # Reset error counter on success
                consecutive_errors = 0
                
                # Wait for next poll
                logger.info(f"Next poll in {POLL_INTERVAL} seconds...")
                time.sleep(POLL_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("Gmail Watcher stopped by user")
                self._save_state()
                break
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in main loop ({consecutive_errors}/{max_errors}): {e}")
                
                if consecutive_errors >= max_errors:
                    logger.error("Too many consecutive errors. Exiting.")
                    self._save_state()
                    break
                
                # Exponential backoff
                wait_time = min(300, POLL_INTERVAL * consecutive_errors)
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)


def main():
    """Entry point."""
    watcher = GmailWatcher()
    watcher.run()


if __name__ == '__main__':
    main()
