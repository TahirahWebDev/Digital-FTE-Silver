"""
Logic Bridge - Discord Autonomous Business Agent

Watches the 04_Approved folder and autonomously:
1. Posts to Discord using WEBHOOK_URL
2. Moves successfully posted files to 05_Done

Error Handling:
- Files move to 07_Reviewing only if Discord posting fails
- Updates Business_Report.md after every post

Silver Tier Compatibility:
- Does NOT delete or modify Silver Tier code
- Extends functionality for Gold Tier
"""

# Fix Windows console encoding for Unicode characters
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
import sys
import time
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add parent directory to path for direct script execution
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.config import (
    SILVER_APPROVED_FOLDER as APPROVED_FOLDER,
    SILVER_DONE_FOLDER as DONE_FOLDER,
    SUPPORTED_EXTENSIONS,
    VAULT_PATH,
    REVIEWING_FOLDER,
    REVIEWING_PATH
)

# Import Gold Tier tools
from scripts.tools.publisher import publish_content as discord_publish
from scripts.tools.auditor import BusinessAuditor

# Import Gold Tier utilities
from scripts.utils.audit_logger import AuditLogger, ActionType, ActionStatus


class GoldTierPublisher:
    """
    Handles publishing to Discord.

    Implements autonomous business operations:
    - Posts to Discord
    - Moves files to 05_Done on success
    - Error handling with file routing to 07_Reviewing
    """

    def __init__(self):
        """Initialize the Gold Tier Publisher."""
        self.auditor = BusinessAuditor()
        self.audit_logger = AuditLogger()
    
    def post_to_discord(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        Post content to Discord.
        
        Args:
            content: Content to post
            file_path: Source file path
            
        Returns:
            Dict with post result
        """
        # Log attempt
        self.audit_logger.log_action(
            action_type=ActionType.DISCORD_POST,
            description="Starting Discord post",
            status=ActionStatus.PENDING,
            details={"file_path": file_path}
        )
        
        # Post to Discord
        result = discord_publish(content)
        
        if result:
            self.audit_logger.log_discord_post(content=content, success=True)
            return {
                "success": True,
                "platform": "discord",
                "content_used": "original"
            }
        else:
            self.audit_logger.log_discord_post(content=content, success=False)
            return {
                "success": False,
                "platform": "discord",
                "error": "Discord publish returned False"
            }

    def process_task(
        self,
        content: str,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Process a task: post to Discord.

        Args:
            content: Task content
            file_path: Source file path

        Returns:
            Dict with overall processing result
        """
        task_name = Path(file_path).stem

        results = {
            "file_path": file_path,
            "task_name": task_name,
            "discord": {"success": False},
            "overall_success": False,
            "errors": []
        }

        platforms_posted = []

        # Post to Discord
        print(f"📢 Posting to Discord...")
        discord_result = self.post_to_discord(content, file_path)
        results["discord"] = discord_result
        if discord_result["success"]:
            platforms_posted.append("discord")

        # Determine overall success
        results["overall_success"] = discord_result["success"]

        # Update Business Report
        self.auditor.update_report(
            task_name=task_name,
            platforms=platforms_posted,
            xero_amount=0,
            xero_success=True,
            post_success=results["overall_success"],
            error_message=results["errors"][0] if results["errors"] else None
        )

        return results


class GoldTierFolderHandler(FileSystemEventHandler):
    """
    Handles file events in the 04_Approved folder.

    Gold Tier Autonomous Logic:
    - Watches 04_Approved for new files
    - Processes each file (Discord posting)
    - On success: moves to 05_Done
    - On failure: moves to 07_Reviewing
    """
    
    def __init__(self):
        """Initialize handler with Gold Tier publisher."""
        self.publisher = GoldTierPublisher()
        self.processed_files = set()  # Track already processed files
    
    def on_created(self, event):
        """Called when a file is created in approved folder."""
        print(f"DEBUG: File event detected: {event.event_type} - {event.src_path}")
        if not event.is_directory:
            file_path = Path(event.src_path)
            print(f"DEBUG: File path: {file_path}, Suffix: {file_path.suffix}")
            if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                if str(file_path) not in self.processed_files:
                    print(f"DEBUG: Processing file: {file_path}")
                    self.processed_files.add(str(file_path))
                    self.process_file(file_path)
                else:
                    print(f"DEBUG: File already processed: {file_path}")
            else:
                print(f"DEBUG: Skipping file - wrong extension: {file_path.suffix}")

    def on_moved(self, event):
        """Called when a file is moved to approved folder."""
        print(f"DEBUG: File moved event detected: {event.event_type} - {event.dest_path}")
        if not event.is_directory:
            dest_path = Path(event.dest_path)
            print(f"DEBUG: Dest path: {dest_path}, Suffix: {dest_path.suffix}")
            if dest_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                if str(dest_path) not in self.processed_files:
                    print(f"DEBUG: Processing moved file: {dest_path}")
                    self.processed_files.add(str(dest_path))
                    self.process_file(dest_path)
    
    def poll_for_new_files(self, approved_path: Path):
        """Poll the approved folder for new files (fallback for missed events)."""
        if not approved_path.exists():
            return
        
        try:
            files = list(approved_path.glob("*.md")) + list(approved_path.glob("*.txt"))
            for file_path in files:
                if str(file_path) not in self.processed_files:
                    print(f"POLL: Found new file: {file_path}")
                    self.processed_files.add(str(file_path))
                    self.process_file(file_path)
        except Exception as e:
            print(f"POLL: Error scanning folder: {e}")
    
    def process_file(self, file_path: Path):
        """
        Process an approved file through Gold Tier workflow.
        
        Args:
            file_path: Path to the file
        """
        print(f"\n{'='*60}")
        print(f"🤖 Gold Tier Autonomous Agent Processing: {file_path.name}")
        print(f"{'='*60}")
        
        # Read content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return
        
        # Process through Gold Tier
        results = self.publisher.process_task(
            content=content,
            file_path=str(file_path)
        )
        
        # Report results
        print(f"\n{'='*60}")
        print(f"📊 Processing Results: {file_path.name}")
        print(f"{'='*60}")
        
        # Discord status
        if results["discord"]["success"]:
            print(f"✅ Discord: Success")
            print(f"📁 Moving file to 05_Done...")
        else:
            print(f"❌ Discord: Failed - {results['discord'].get('error', 'Unknown')}")
            print(f"⚠️  Moving file to 07_Reviewing...")

        # Determine destination based on success/failure
        if results["overall_success"]:
            # Move to Done if Discord succeeded
            self._move_to_done(file_path)
        else:
            # Nothing succeeded - move to Reviewing
            self._move_to_reviewing(file_path, "Discord posting failed")

        print(f"{'='*60}\n")

    def _move_to_done(self, file_path: Path):
        """Move file to 05_Done folder."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        done_folder = Path(DONE_FOLDER)
        done_folder.mkdir(exist_ok=True)
        
        new_filename = f"{file_path.stem}_posted_{timestamp}{file_path.suffix}"
        new_path = done_folder / new_filename
        
        try:
            shutil.move(str(file_path), str(new_path))
            print(f"📁 File moved to Done: {new_filename}")
        except Exception as e:
            print(f"❌ Error moving file: {e}")
    
    def _move_to_reviewing(self, file_path: Path, reason: str):
        """
        Move file to 07_Reviewing folder on failure.
        
        Args:
            file_path: Path to the file
            reason: Reason for moving to reviewing
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reviewing_folder = REVIEWING_PATH
        reviewing_folder.mkdir(parents=True, exist_ok=True)
        
        new_filename = f"{file_path.stem}_review_{timestamp}{file_path.suffix}"
        new_path = reviewing_folder / new_filename
        
        try:
            shutil.move(str(file_path), str(new_path))
            print(f"⚠️  File moved to Reviewing: {new_filename}")
            print(f"   Reason: {reason}")
        except Exception as e:
            print(f"❌ Error moving file: {e}")


def ensure_gold_tier_folders():
    """Ensure all Gold Tier folders exist."""
    from scripts.config import GOLD_TIER_FOLDERS
    
    for folder in GOLD_TIER_FOLDERS:
        folder.mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Gold Tier folders verified")


def start_logic_bridge():
    """Start the Gold Tier Logic Bridge."""
    # Ensure folders exist
    ensure_gold_tier_folders()

    # Create observer
    observer = Observer()
    handler = GoldTierFolderHandler()

    # Get approved folder path
    approved_path = Path(APPROVED_FOLDER).resolve()

    if not approved_path.exists():
        print(f"Creating approved folder: {approved_path}")
        approved_path.mkdir(parents=True, exist_ok=True)

    # Start watching
    observer.schedule(handler, str(approved_path), recursive=False)
    observer.start()

    # Print startup message
    print(f"\n{'='*60}")
    print(f"🤖 Gold Tier Autonomous Business Agent Started")
    print(f"{'='*60}")
    print(f"📁 Watching: {approved_path}")
    print(f"📢 Platform: Discord")
    print(f"📁 Auto-move: Files → 05_Done on success")
    print(f"📝 Business Report: 00_CEO_Briefings/Business_Report.md")
    print(f"\nPress Ctrl+C to stop...")
    print(f"{'='*60}\n")

    try:
        poll_counter = 0
        while True:
            time.sleep(1)
            poll_counter += 1
            # Poll for new files every 5 seconds (fallback for missed events)
            if poll_counter >= 5:
                handler.poll_for_new_files(approved_path)
                poll_counter = 0
    except KeyboardInterrupt:
        observer.stop()
        print("\n🛑 Stopping Gold Tier Logic Bridge...")

    observer.join()
    print("Logic Bridge stopped.")


if __name__ == "__main__":
    start_logic_bridge()
