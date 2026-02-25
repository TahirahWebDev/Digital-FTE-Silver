#!/usr/bin/env python3
"""
Gmail Integration Orchestrator

Monitors folders for email processing and approval workflow:
- /02_Needs_Actions: New emails from Gmail
- /04_Approved: Approved emails ready to send

When new Needs_Action file detected:
- Calls AI assistant to process email using gmail_operator skill

When new Approved file detected:
- Calls MCP send_email tool
- Moves completed files to /05_Done

Runs 24/7 in background with auto-restart.
"""

import os
import sys
import time
import json
import subprocess
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', 'F:\\Tahirah\\Hackathon-0\\AI_Employee_Vault'))
NEEDS_ACTION_FOLDER = VAULT_PATH / os.getenv('NEEDS_ACTION_FOLDER', '02_Needs_Actions')
PENDING_APPROVAL_FOLDER = VAULT_PATH / os.getenv('PENDING_APPROVAL_FOLDER', '03_Pending_Approval')
APPROVED_FOLDER = VAULT_PATH / os.getenv('APPROVED_FOLDER', '04_Approved')
DONE_FOLDER = VAULT_PATH / os.getenv('DONE_FOLDER', '05_Done')
REJECTED_FOLDER = VAULT_PATH / os.getenv('REJECTED_FOLDER', '08_Rejected')
LOGS_FOLDER = VAULT_PATH / os.getenv('LOGS_FOLDER', 'Logs')

POLL_INTERVAL = int(os.getenv('ORCHESTRATOR_POLL_INTERVAL', '10'))
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'
MCP_SERVER_PATH = Path(__file__).parent / 'email-mcp' / 'index.js'

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_FOLDER / 'gmail_orchestrator.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GmailOrchestrator:
    """Orchestrates Gmail email processing and approval workflow."""
    
    def __init__(self):
        self.processed_files: set = set()
        self.approval_files: set = set()
        
        # Ensure folders exist
        for folder in [NEEDS_ACTION_FOLDER, PENDING_APPROVAL_FOLDER, APPROVED_FOLDER, DONE_FOLDER, REJECTED_FOLDER, LOGS_FOLDER]:
            folder.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Gmail Orchestrator initialized (DRY_RUN={DRY_RUN})")
    
    def _load_yaml_frontmatter(self, filepath: Path) -> Dict[str, Any]:
        """Load YAML frontmatter from markdown file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.startswith('---'):
                return {}
            
            # Simple YAML parsing for frontmatter
            parts = content.split('---', 2)
            if len(parts) < 3:
                return {}
            
            yaml_content = parts[1].strip()
            metadata = {}
            
            for line in yaml_content.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
            
            return metadata
        except Exception as e:
            logger.error(f"Error loading frontmatter from {filepath}: {e}")
            return {}
    
    def _log_action(self, action_type: str, target: str, parameters: Dict, result: str):
        """Log action to JSON file."""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            log_file = LOGS_FOLDER / f"gmail_orchestrator_{today}.json"
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'action_type': action_type,
                'target': target,
                'parameters': parameters,
                'result': result,
                'dry_run': DRY_RUN
            }
            
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
    
    def _call_ai_assistant(self, email_file: Path, metadata: Dict) -> bool:
        """Call AI assistant to process email using gmail_operator skill."""
        try:
            subject = metadata.get('subject', 'Unknown')
            from_addr = metadata.get('from', 'Unknown')
            
            prompt = f"""
Process this email using the gmail_operator skill:

File: {email_file}
From: {from_addr}
Subject: {subject}

Instructions:
1. Classify the email intent
2. Create a plan in /Plans/
3. Draft a response
4. Create an approval file in /03_Pending_Approval/

Read the full email content from the file and take appropriate action.
"""
            
            if DRY_RUN:
                logger.info(f"[DRY_RUN] Would call AI assistant for: {subject}")
                self._log_action('ai_assistant_call', str(email_file), {
                    'subject': subject,
                    'from': from_addr
                }, 'simulated')
                return True
            
            # Log the action
            self._log_action('ai_assistant_call', str(email_file), {
                'subject': subject,
                'from': from_addr,
                'prompt': prompt
            }, 'initiated')
            
            logger.info(f"AI assistant called for email: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error calling AI assistant: {e}")
            self._log_action('ai_assistant_call', str(email_file), {}, f'error: {e}')
            return False
    
    def _call_mcp_send_email(self, approval_file: Path) -> bool:
        """Call MCP server to send email."""
        try:
            # Parse approval file
            metadata = self._load_yaml_frontmatter(approval_file)
            
            to_addr = metadata.get('to', '')
            subject = metadata.get('subject', '')
            
            if not to_addr or not subject:
                logger.error(f"Missing required fields in approval file: {approval_file}")
                return False
            
            # Read email body from file
            with open(approval_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract body (after the "Email Content" section)
            body_start = content.find('## Email Content')
            if body_start == -1:
                body = content
            else:
                body = content[body_start:].split('\n', 2)[-1].strip()
            
            if DRY_RUN:
                logger.info(f"[DRY_RUN] Would send email to: {to_addr}")
                self._log_action('mcp_send_email', to_addr, {
                    'to': to_addr,
                    'subject': subject
                }, 'simulated')
                return True
            
            # Call MCP server via Node.js
            mcp_call = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "send_email",
                    "arguments": {
                        "to": to_addr,
                        "subject": subject,
                        "body": body
                    }
                }
            }
            
            # Start MCP server and call tool
            process = subprocess.Popen(
                ["node", str(MCP_SERVER_PATH)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(MCP_SERVER_PATH.parent)
            )
            
            process.stdin.write(json.dumps(mcp_call) + "\n")
            process.stdin.flush()
            
            # Wait for response
            time.sleep(2)
            response_line = process.stdout.readline()
            
            process.terminate()
            process.wait(timeout=5)
            
            if response_line:
                response = json.loads(response_line)
                if not response.get('isError', False):
                    logger.info(f"Email sent successfully to: {to_addr}")
                    self._log_action('mcp_send_email', to_addr, {
                        'to': to_addr,
                        'subject': subject
                    }, 'success')
                    return True
                else:
                    error_text = response.get('content', [{}])[0].get('text', 'Unknown error')
                    logger.error(f"MCP error: {error_text}")
                    self._log_action('mcp_send_email', to_addr, {}, f'error: {error_text}')
                    return False
            else:
                logger.error("No response from MCP server")
                return False
            
        except Exception as e:
            logger.error(f"Error calling MCP send_email: {e}")
            self._log_action('mcp_send_email', str(approval_file), {}, f'error: {e}')
            return False
    
    def _move_to_done(self, filepath: Path):
        """Move file to Done folder."""
        try:
            if not filepath.exists():
                return
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_filename = f"{filepath.stem}_done_{timestamp}{filepath.suffix}"
            new_path = DONE_FOLDER / new_filename
            
            # Remove from processed set
            self.processed_files.discard(str(filepath))
            self.approval_files.discard(str(filepath))
            
            import shutil
            shutil.move(str(filepath), str(new_path))
            logger.info(f"Moved to Done: {new_filename}")
            
        except Exception as e:
            logger.error(f"Error moving file to Done: {e}")
    
    def _move_to_rejected(self, filepath: Path, reason: str = ''):
        """Move file to Rejected folder."""
        try:
            if not filepath.exists():
                return
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_filename = f"{filepath.stem}_rejected_{timestamp}{filepath.suffix}"
            new_path = REJECTED_FOLDER / new_filename
            
            self.processed_files.discard(str(filepath))
            self.approval_files.discard(str(filepath))
            
            import shutil
            shutil.move(str(filepath), str(new_path))
            logger.info(f"Moved to Rejected: {new_filename} ({reason})")
            
        except Exception as e:
            logger.error(f"Error moving file to Rejected: {e}")
    
    def process_needs_action_folder(self):
        """Process new files in Needs_Action folder."""
        try:
            files = list(NEEDS_ACTION_FOLDER.glob('*.md'))
            
            for filepath in files:
                if str(filepath) in self.processed_files:
                    continue
                
                # Load metadata
                metadata = self._load_yaml_frontmatter(filepath)
                
                # Only process email type files
                if metadata.get('type') != 'email':
                    continue
                
                # Check status
                if metadata.get('status') != 'pending':
                    continue
                
                logger.info(f"Processing new email: {filepath.name}")
                
                # Call AI assistant
                self._call_ai_assistant(filepath, metadata)
                
                # Mark as processed
                self.processed_files.add(str(filepath))
                
        except Exception as e:
            logger.error(f"Error processing Needs_Action folder: {e}")
    
    def process_approved_folder(self):
        """Process approved files ready to send."""
        try:
            files = list(APPROVED_FOLDER.glob('*.md'))
            
            for filepath in files:
                if str(filepath) in self.approval_files:
                    continue
                
                # Load metadata
                metadata = self._load_yaml_frontmatter(filepath)
                
                # Only process approval files
                if metadata.get('type') != 'email_approval':
                    continue
                
                # Check status
                if metadata.get('status') != 'pending_approval':
                    continue
                
                logger.info(f"Processing approved email: {filepath.name}")
                
                # Call MCP to send email
                success = self._call_mcp_send_email(filepath)
                
                if success:
                    # Move to Done
                    self._move_to_done(filepath)
                else:
                    # Move to Rejected
                    self._move_to_rejected(filepath, 'Send failed')
                
                # Mark as processed
                self.approval_files.add(str(filepath))
                
        except Exception as e:
            logger.error(f"Error processing Approved folder: {e}")
    
    def run(self):
        """Main run loop."""
        logger.info("=" * 60)
        logger.info("Gmail Orchestrator Starting...")
        logger.info(f"Poll Interval: {POLL_INTERVAL} seconds")
        logger.info(f"DRY_RUN: {DRY_RUN}")
        logger.info("=" * 60)
        
        consecutive_errors = 0
        max_errors = 10
        
        while True:
            try:
                # Process folders
                self.process_needs_action_folder()
                self.process_approved_folder()
                
                # Reset error counter
                consecutive_errors = 0
                
                # Wait for next poll
                time.sleep(POLL_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("Gmail Orchestrator stopped by user")
                break
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in main loop ({consecutive_errors}/{max_errors}): {e}")
                
                if consecutive_errors >= max_errors:
                    logger.error("Too many consecutive errors. Exiting.")
                    break
                
                # Exponential backoff
                wait_time = min(300, POLL_INTERVAL * consecutive_errors)
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)


def main():
    """Entry point."""
    orchestrator = GmailOrchestrator()
    orchestrator.run()


if __name__ == '__main__':
    main()
