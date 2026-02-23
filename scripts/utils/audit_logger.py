"""
Audit Logger - Records all actions to audit_log.md in Obsidian vault.

This module provides comprehensive audit logging for the Gold Tier system.
Every action (post, log, error, recovery) is recorded for traceability.

Usage:
    from scripts.utils.audit_logger import AuditLogger
    
    audit = AuditLogger()
    
    # Log an action
    audit.log_action(
        action_type="twitter_post",
        description="Posted content to Twitter",
        status="success",
        details={"tweet_id": "123456"}
    )
    
    # Log task completion
    audit.log_task_completion(
        task_name="Social Media Post",
        file_path="05_Done/post.md",
        platforms=["discord", "twitter"],
        xero_logged=True
    )
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

from scripts.config import AUDIT_LOG_PATH, VAULT_PATH, AUDIT_LOGGING_ENABLED

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of actions that can be logged."""
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    DISCORD_POST = "discord_post"
    TWITTER_POST = "twitter_post"
    XERO_LOG = "xero_log"
    RESEARCH = "research"
    ERROR = "error"
    RECOVERY = "recovery"
    AUDIT = "audit"
    FILE_MOVE = "file_move"
    APPROVAL = "approval"
    CUSTOM = "custom"


class ActionStatus(Enum):
    """Status of an action."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    PENDING = "pending"
    RETRY = "retry"


@dataclass
class AuditEntry:
    """A single audit log entry."""
    timestamp: str
    action_type: str
    status: str
    description: str
    details: Dict[str, Any]
    file_path: str = ""
    user: str = "ai_employee"
    session_id: str = ""


class AuditLogger:
    """
    Comprehensive audit logging for the Gold Tier system.
    
    Records all actions to audit_log.md in the Obsidian vault
    for traceability and compliance.
    """
    
    def __init__(
        self,
        audit_log_path: Optional[Path] = None,
        enabled: bool = True
    ):
        """
        Initialize the Audit Logger.
        
        Args:
            audit_log_path: Path to audit log. Uses config if not provided.
            enabled: Whether audit logging is enabled
        """
        self.audit_log_path = audit_log_path or (AUDIT_LOG_PATH / "audit_log.md")
        self.enabled = enabled and AUDIT_LOGGING_ENABLED

        # Generate session ID first (used in initialization)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Ensure audit log directory exists
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

        # Create audit log file if it doesn't exist
        if not self.audit_log_path.exists():
            self._initialize_audit_log()

        logger.info("Audit Logger initialized. Log path: %s", self.audit_log_path)
    
    def _initialize_audit_log(self) -> None:
        """
        Initialize the audit log file with header.
        """
        header = f"""---
title: "AI Employee Vault - Audit Log"
created: "{datetime.now().isoformat()}"
tags: [audit-log, compliance, tracking]
category: system
---

# 📋 AI Employee Vault - Audit Log

**Vault:** {VAULT_PATH}  
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Session:** {self.session_id}

---

## Audit Entries

"""
        try:
            with open(self.audit_log_path, 'w', encoding='utf-8') as f:
                f.write(header)
        except Exception as e:
            logger.error("Failed to initialize audit log: %s", str(e))
    
    def _format_entry(self, entry: AuditEntry) -> str:
        """
        Format an audit entry as markdown.
        
        Args:
            entry: The audit entry to format
            
        Returns:
            Formatted markdown string
        """
        # Format timestamp as heading
        time_str = entry.timestamp.split('T')[1].split('.')[0] if 'T' in entry.timestamp else entry.timestamp
        
        # Status emoji
        status_emoji = {
            "success": "✅",
            "failure": "❌",
            "partial": "⚠️",
            "pending": "⏳",
            "retry": "🔄"
        }.get(entry.status, "📝")
        
        # Action type emoji
        action_emoji = {
            "task_start": "🚀",
            "task_complete": "✅",
            "discord_post": "💬",
            "twitter_post": "🐦",
            "xero_log": "📊",
            "research": "🔍",
            "error": "❌",
            "recovery": "🔄",
            "audit": "📋",
            "file_move": "📁",
            "approval": "✓"
        }.get(entry.action_type, "📝")
        
        # Build the entry
        formatted = f"""
### {status_emoji} {action_emoji} [{entry.action_type.upper()}] {time_str}

**Status:** {entry.status.upper()}  
**Description:** {entry.description}  
**User:** {entry.user}  
**Session:** {entry.session_id}
"""
        
        if entry.file_path:
            formatted += f"**File:** `{entry.file_path}`  \n"
        
        # Add details as a table if present
        if entry.details:
            formatted += "\n**Details:**\n"
            formatted += "| Key | Value |\n"
            formatted += "|-----|-------|\n"
            for key, value in entry.details.items():
                value_str = str(value)
                # Truncate long values
                if len(value_str) > 100:
                    value_str = value_str[:97] + "..."
                formatted += f"| {key} | {value_str} |\n"
        
        formatted += "\n---\n"
        
        return formatted
    
    def log_action(
        self,
        action_type: ActionType,
        description: str,
        status: ActionStatus,
        details: Optional[Dict[str, Any]] = None,
        file_path: Optional[str] = None
    ) -> AuditEntry:
        """
        Log an action to the audit log.
        
        Args:
            action_type: Type of action
            description: Description of the action
            status: Status of the action
            details: Optional additional details
            file_path: Optional related file path
            
        Returns:
            The created AuditEntry
        """
        if not self.enabled:
            logger.debug("Audit logging disabled. Skipping: %s", action_type.value)
            return None
        
        timestamp = datetime.now().isoformat()
        
        entry = AuditEntry(
            timestamp=timestamp,
            action_type=action_type.value,
            status=status.value,
            description=description,
            details=details or {},
            file_path=file_path or "",
            user="ai_employee",
            session_id=self.session_id
        )
        
        # Format and write entry
        formatted_entry = self._format_entry(entry)
        
        try:
            with open(self.audit_log_path, 'a', encoding='utf-8') as f:
                f.write(formatted_entry)
            
            logger.debug("Audit entry logged: %s - %s", action_type.value, status.value)
            
        except Exception as e:
            logger.error("Failed to write audit entry: %s", str(e))
        
        return entry
    
    def log_task_start(
        self,
        task_name: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEntry:
        """
        Log the start of a task.
        
        Args:
            task_name: Name of the task
            file_path: Path to the task file
            metadata: Optional task metadata
            
        Returns:
            AuditEntry
        """
        details = {"task_name": task_name, **(metadata or {})}
        
        return self.log_action(
            action_type=ActionType.TASK_START,
            description=f"Starting task: {task_name}",
            status=ActionStatus.PENDING,
            details=details,
            file_path=file_path
        )
    
    def log_task_completion(
        self,
        task_name: str,
        file_path: str,
        platforms: Optional[List[str]] = None,
        xero_logged: bool = False,
        duration_seconds: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEntry:
        """
        Log the completion of a task.
        
        Args:
            task_name: Name of the completed task
            file_path: Path to the task file
            platforms: List of platforms posted to
            xero_logged: Whether task was logged to Xero
            duration_seconds: Task duration
            metadata: Optional additional metadata
            
        Returns:
            AuditEntry
        """
        details = {
            "task_name": task_name,
            "platforms": platforms or [],
            "xero_logged": xero_logged,
            **(metadata or {})
        }
        
        if duration_seconds is not None:
            details["duration_seconds"] = round(duration_seconds, 2)
        
        return self.log_action(
            action_type=ActionType.TASK_COMPLETE,
            description=f"Task completed: {task_name}",
            status=ActionStatus.SUCCESS,
            details=details,
            file_path=file_path
        )
    
    def log_discord_post(
        self,
        content: str,
        success: bool,
        webhook_response: Optional[str] = None,
        error: Optional[str] = None
    ) -> AuditEntry:
        """
        Log a Discord post attempt.
        
        Args:
            content: Content that was posted
            success: Whether the post succeeded
            webhook_response: Response from webhook
            error: Error message if failed
            
        Returns:
            AuditEntry
        """
        details = {
            "content_preview": content[:100] if content else "",
            "content_length": len(content) if content else 0
        }
        
        if webhook_response:
            details["webhook_response"] = webhook_response
        if error:
            details["error"] = error
        
        return self.log_action(
            action_type=ActionType.DISCORD_POST,
            description="Discord post attempt",
            status=ActionStatus.SUCCESS if success else ActionStatus.FAILURE,
            details=details
        )
    
    def log_twitter_post(
        self,
        content: str,
        success: bool,
        tweet_id: Optional[str] = None,
        error: Optional[str] = None,
        simplified: bool = False
    ) -> AuditEntry:
        """
        Log a Twitter post attempt.
        
        Args:
            content: Content that was posted
            success: Whether the post succeeded
            tweet_id: Twitter tweet ID if successful
            error: Error message if failed
            simplified: Whether simplified content was used
            
        Returns:
            AuditEntry
        """
        details = {
            "content_preview": content[:100] if content else "",
            "content_length": len(content) if content else 0,
            "simplified": simplified
        }
        
        if tweet_id:
            details["tweet_id"] = tweet_id
            details["url"] = f"https://twitter.com/user/status/{tweet_id}"
        if error:
            details["error"] = error
        
        return self.log_action(
            action_type=ActionType.TWITTER_POST,
            description="Twitter/X post attempt",
            status=ActionStatus.SUCCESS if success else ActionStatus.FAILURE,
            details=details
        )
    
    def log_xero_entry(
        self,
        task_name: str,
        entry_type: str,
        success: bool,
        reference: Optional[str] = None,
        amount: float = 0.0,
        error: Optional[str] = None
    ) -> AuditEntry:
        """
        Log a Xero accounting entry.
        
        Args:
            task_name: Name of the task being logged
            entry_type: "journal" or "invoice"
            success: Whether the logging succeeded
            reference: Xero reference number
            amount: Monetary amount
            error: Error message if failed
            
        Returns:
            AuditEntry
        """
        details = {
            "task_name": task_name,
            "entry_type": entry_type,
            "amount": amount
        }
        
        if reference:
            details["reference"] = reference
        if error:
            details["error"] = error
        
        return self.log_action(
            action_type=ActionType.XERO_LOG,
            description=f"Xero {entry_type} for: {task_name}",
            status=ActionStatus.SUCCESS if success else ActionStatus.FAILURE,
            details=details
        )
    
    def log_error(
        self,
        operation: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AuditEntry:
        """
        Log an error occurrence.
        
        Args:
            operation: Operation that failed
            error_message: Error message
            context: Additional context
            
        Returns:
            AuditEntry
        """
        details = {
            "operation": operation,
            "error_message": error_message,
            **(context or {})
        }
        
        return self.log_action(
            action_type=ActionType.ERROR,
            description=f"Error in {operation}",
            status=ActionStatus.FAILURE,
            details=details
        )
    
    def log_recovery(
        self,
        operation: str,
        recovery_method: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEntry:
        """
        Log a recovery attempt.
        
        Args:
            operation: Operation being recovered
            recovery_method: Method used for recovery
            success: Whether recovery succeeded
            details: Additional details
            
        Returns:
            AuditEntry
        """
        details = {
            "operation": operation,
            "recovery_method": recovery_method,
            **(details or {})
        }
        
        return self.log_action(
            action_type=ActionType.RECOVERY,
            description=f"Recovery attempt for {operation}",
            status=ActionStatus.SUCCESS if success else ActionStatus.FAILURE,
            details=details
        )
    
    def log_research(
        self,
        topic: str,
        sources_found: int,
        duration_seconds: float
    ) -> AuditEntry:
        """
        Log a research operation.
        
        Args:
            topic: Research topic
            sources_found: Number of sources found
            duration_seconds: Research duration
            
        Returns:
            AuditEntry
        """
        details = {
            "topic": topic,
            "sources_found": sources_found,
            "duration_seconds": round(duration_seconds, 2)
        }
        
        return self.log_action(
            action_type=ActionType.RESEARCH,
            description=f"Research completed: {topic}",
            status=ActionStatus.SUCCESS,
            details=details
        )
    
    def log_file_move(
        self,
        source: str,
        destination: str,
        success: bool,
        error: Optional[str] = None
    ) -> AuditEntry:
        """
        Log a file move operation.
        
        Args:
            source: Source file path
            destination: Destination path
            success: Whether the move succeeded
            error: Error message if failed
            
        Returns:
            AuditEntry
        """
        details = {
            "source": source,
            "destination": destination
        }
        
        if error:
            details["error"] = error
        
        return self.log_action(
            action_type=ActionType.FILE_MOVE,
            description=f"File move: {Path(source).name}",
            status=ActionStatus.SUCCESS if success else ActionStatus.FAILURE,
            details=details,
            file_path=source
        )
    
    def get_recent_entries(
        self,
        limit: int = 10,
        action_type: Optional[ActionType] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent audit entries.
        
        Args:
            limit: Maximum number of entries to return
            action_type: Optional filter by action type
            
        Returns:
            List of recent entries
        """
        if not self.audit_log_path.exists():
            return []
        
        try:
            with open(self.audit_log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple parsing - count entries
            entries = []
            entry_starts = [i for i, line in enumerate(content.split('\n')) 
                          if line.startswith('### ')]
            
            # Get last N entries
            recent_starts = entry_starts[-limit:] if len(entry_starts) > limit else entry_starts
            
            lines = content.split('\n')
            for start_idx in recent_starts:
                # Find end of this entry
                end_idx = start_idx + 1
                while end_idx < len(lines) and not lines[end_idx].startswith('### '):
                    end_idx += 1
                
                entry_text = '\n'.join(lines[start_idx:end_idx])
                
                # Parse entry (simplified)
                if action_type is None or action_type.value.upper() in entry_text:
                    entries.append({
                        "raw": entry_text,
                        "action_type": action_type.value if action_type else "unknown"
                    })
            
            return entries
            
        except Exception as e:
            logger.error("Failed to read audit entries: %s", str(e))
            return []
    
    def get_daily_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a summary of actions for a specific date.
        
        Args:
            date: Date string (YYYY-MM-DD). Defaults to today.
            
        Returns:
            Dict with daily summary
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        if not self.audit_log_path.exists():
            return {"error": "No audit log found"}
        
        try:
            with open(self.audit_log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count by status
            status_counts = {}
            action_counts = {}
            total = 0
            
            for line in content.split('\n'):
                if date in line:
                    # Check if this date is in an entry header
                    if line.startswith('### '):
                        total += 1
                    
                    if '**Status:**' in line:
                        status = line.split('**Status:**')[1].strip().upper()
                        status_counts[status] = status_counts.get(status, 0) + 1
                    
                    if '] ' in line and line.startswith('### '):
                        action = line.split(']')[0].split('[')[1].strip().lower()
                        action_counts[action] = action_counts.get(action, 0) + 1
            
            return {
                "date": date,
                "total_actions": total,
                "by_status": status_counts,
                "by_action": action_counts,
                "success_rate": round(
                    status_counts.get('SUCCESS', 0) / total * 100, 1
                ) if total > 0 else 0
            }
            
        except Exception as e:
            logger.error("Failed to generate daily summary: %s", str(e))
            return {"error": str(e)}


# Convenience functions
def log_action(
    action_type: ActionType,
    description: str,
    status: ActionStatus,
    details: Optional[Dict[str, Any]] = None
) -> AuditEntry:
    """Quick function to log an action."""
    audit = AuditLogger()
    return audit.log_action(action_type, description, status, details)


def log_task_complete(
    task_name: str,
    file_path: str,
    platforms: Optional[List[str]] = None,
    xero_logged: bool = False
) -> AuditEntry:
    """Quick function to log task completion."""
    audit = AuditLogger()
    return audit.log_task_completion(task_name, file_path, platforms, xero_logged)


if __name__ == "__main__":
    # Test the Audit Logger
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Audit Logger...")
    audit = AuditLogger()
    
    # Log various actions
    print("\n1. Logging task start...")
    audit.log_task_start(
        task_name="Social Media Post",
        file_path="01_Inbox/test_post.md"
    )
    
    print("\n2. Logging Discord post...")
    audit.log_discord_post(
        content="Test Discord post content",
        success=True
    )
    
    print("\n3. Logging Twitter post...")
    audit.log_twitter_post(
        content="Test Twitter post content #AI",
        success=True,
        tweet_id="123456789"
    )
    
    print("\n4. Logging Xero entry...")
    audit.log_xero_entry(
        task_name="Social Media Management",
        entry_type="journal",
        success=True,
        reference="TEST-001",
        amount=25.00
    )
    
    print("\n5. Logging task completion...")
    audit.log_task_completion(
        task_name="Social Media Post",
        file_path="05_Done/test_post.md",
        platforms=["discord", "twitter"],
        xero_logged=True
    )
    
    print("\n6. Getting daily summary...")
    summary = audit.get_daily_summary()
    print(f"Daily summary: {summary}")
    
    print(f"\nAudit log written to: {audit.audit_log_path}")
