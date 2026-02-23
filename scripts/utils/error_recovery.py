"""
Error Recovery - Self-correction logic for failed operations.

This module provides error recovery mechanisms for the Gold Tier system.
When Discord or Twitter posts fail, it logs errors and attempts simplified versions.

Usage:
    from scripts.utils.error_recovery import ErrorRecovery
    
    recovery = ErrorRecovery()
    
    # Log an error
    recovery.log_error("Twitter post failed", "Rate limit exceeded")
    
    # Get simplified version of content
    simplified = recovery.get_simplified_version(original_content)
    
    # Check if retry is allowed
    if recovery.can_retry("twitter_post"):
        # Retry with simplified content
        pass
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum

from scripts.config import ERROR_RECOVERY_LOG_PATH, MAX_RETRY_ATTEMPTS, SIMPLIFIED_POST_ENABLED

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can occur."""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    CONTENT_POLICY = "content_policy"
    DUPLICATE = "duplicate"
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class ErrorRecord:
    """Record of a single error occurrence."""
    timestamp: str
    operation: str
    error_message: str
    error_type: ErrorType
    original_content: str = ""
    simplified_content: str = ""
    attempt_number: int = 1
    recovered: bool = False
    recovery_method: str = ""


class ErrorRecovery:
    """
    Handles error logging and recovery strategies.
    
    Provides self-correction capabilities for failed operations
    by logging errors and attempting simplified versions.
    """
    
    def __init__(self, log_path: Optional[Path] = None):
        """
        Initialize the Error Recovery system.
        
        Args:
            log_path: Path to error recovery log. Uses config if not provided.
        """
        self.log_path = log_path or ERROR_RECOVERY_LOG_PATH
        self.max_retries = MAX_RETRY_ATTEMPTS
        self.simplified_enabled = SIMPLIFIED_POST_ENABLED
        
        # Ensure log directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory error tracking
        self.error_counts: Dict[str, int] = {}
        self.last_error_time: Dict[str, datetime] = {}
        
        logger.info("Error Recovery initialized. Log path: %s", self.log_path)
    
    def _detect_error_type(self, error_message: str) -> ErrorType:
        """
        Detect the type of error from the error message.
        
        Args:
            error_message: The error message string
            
        Returns:
            ErrorType enum value
        """
        error_lower = error_message.lower()
        
        if any(x in error_lower for x in ['network', 'connection', 'timeout', 'unreachable']):
            return ErrorType.NETWORK
        elif any(x in error_lower for x in ['auth', 'token', 'credential', 'permission', '401', '403']):
            return ErrorType.AUTHENTICATION
        elif any(x in error_lower for x in ['rate limit', 'too many', '429']):
            return ErrorType.RATE_LIMIT
        elif any(x in error_lower for x in ['policy', 'rules', 'violat', 'inappropriate']):
            return ErrorType.CONTENT_POLICY
        elif 'duplicate' in error_lower:
            return ErrorType.DUPLICATE
        elif any(x in error_lower for x in ['valid', 'invalid', 'format', 'required']):
            return ErrorType.VALIDATION
        elif 'timeout' in error_lower:
            return ErrorType.TIMEOUT
        
        return ErrorType.UNKNOWN
    
    def _create_simplified_version(self, content: str) -> str:
        """
        Create a simplified version of content for error recovery.
        
        Args:
            content: Original content
            
        Returns:
            Simplified content
        """
        import re
        
        simplified = content
        
        # Remove URLs (can cause issues)
        simplified = re.sub(r'http[s]?://\S+', '', simplified)
        
        # Remove hashtags
        simplified = re.sub(r'#\w+', '', simplified)
        
        # Remove mentions
        simplified = re.sub(r'@\w+', '', simplified)
        
        # Remove emojis
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "]+",
            flags=re.UNICODE
        )
        simplified = emoji_pattern.sub('', simplified)
        
        # Remove special characters but keep basic punctuation
        simplified = re.sub(r'[^\w\s\.\,\!\?\-\:\;\']', '', simplified)
        
        # Remove extra whitespace
        simplified = ' '.join(simplified.split())
        
        # Trim to safe length (leave room for Twitter overhead)
        max_length = 250
        if len(simplified) > max_length:
            simplified = simplified[:max_length - 3] + "..."
        
        return simplified.strip()
    
    def log_error(
        self,
        operation: str,
        error_message: str,
        original_content: str = "",
        attempt_number: int = 1
    ) -> ErrorRecord:
        """
        Log an error to the error recovery log.
        
        Args:
            operation: Name of the failed operation
            error_message: The error message
            original_content: Original content that failed
            attempt_number: Which attempt this was
            
        Returns:
            ErrorRecord for the error
        """
        timestamp = datetime.now().isoformat()
        error_type = self._detect_error_type(error_message)
        
        # Create error record
        error_record = ErrorRecord(
            timestamp=timestamp,
            operation=operation,
            error_message=error_message,
            error_type=error_type,
            original_content=original_content,
            attempt_number=attempt_number
        )
        
        # Generate simplified content if applicable
        if self.simplified_enabled and original_content:
            simplified = self._create_simplified_version(original_content)
            error_record.simplified_content = simplified
        
        # Write to log file
        self._write_error_log(error_record)
        
        # Update in-memory tracking
        self._track_error(operation)
        
        logger.warning("Error logged: %s - %s (attempt %d)", 
                      operation, error_type.value, attempt_number)
        
        return error_record
    
    def _write_error_log(self, error_record: ErrorRecord) -> None:
        """
        Write error record to the log file.
        
        Args:
            error_record: The error record to log
        """
        log_entry = f"""
{'=' * 60}
TIMESTAMP: {error_record.timestamp}
OPERATION: {error_record.operation}
ERROR TYPE: {error_record.error_type.value}
ATTEMPT: {error_record.attempt_number}
ERROR MESSAGE: {error_record.error_message}
RECOVERED: {error_record.recovered}
RECOVERY METHOD: {error_record.recovery_method}
{'-' * 60}
ORIGINAL CONTENT:
{error_record.original_content[:500] if error_record.original_content else 'N/A'}
{'-' * 60}
SIMPLIFIED CONTENT:
{error_record.simplified_content if error_record.simplified_content else 'N/A'}
{'=' * 60}

"""
        
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            logger.error("Failed to write error log: %s", str(e))
    
    def _track_error(self, operation: str) -> None:
        """
        Track error counts in memory for rate limiting.
        
        Args:
            operation: Operation name
        """
        if operation not in self.error_counts:
            self.error_counts[operation] = 0
            self.last_error_time[operation] = datetime.now()
        
        self.error_counts[operation] += 1
        self.last_error_time[operation] = datetime.now()
    
    def can_retry(self, operation: str) -> bool:
        """
        Check if an operation can be retried.
        
        Args:
            operation: Operation name
            
        Returns:
            True if retry is allowed
        """
        count = self.error_counts.get(operation, 0)
        return count < self.max_retries
    
    def get_retry_delay(self, operation: str) -> int:
        """
        Get recommended delay before retry (exponential backoff).
        
        Args:
            operation: Operation name
            
        Returns:
            Delay in seconds
        """
        count = self.error_counts.get(operation, 0)
        # Exponential backoff: 1s, 2s, 4s, 8s, etc.
        return min(2 ** count, 60)  # Cap at 60 seconds
    
    def get_simplified_version(self, content: str, remove_media: bool = True) -> Dict[str, Any]:
        """
        Get a simplified version of content for retry.
        
        Args:
            content: Original content
            remove_media: Whether to indicate media should be removed
            
        Returns:
            Dict with simplified content and metadata
        """
        simplified = self._create_simplified_version(content)
        
        return {
            "original": content,
            "simplified": simplified,
            "original_length": len(content),
            "simplified_length": len(simplified),
            "reduction_percent": round((1 - len(simplified) / len(content)) * 100, 1) if content else 0,
            "media_removed": remove_media,
            "changes_applied": [
                "Removed URLs",
                "Removed hashtags",
                "Removed mentions",
                "Removed emojis",
                "Removed special characters",
                "Trimmed to safe length"
            ]
        }
    
    def attempt_recovery(
        self,
        operation: str,
        original_content: str,
        error_message: str,
        retry_function: Callable[[str], Any],
        attempt_number: int = 1
    ) -> Dict[str, Any]:
        """
        Attempt to recover from an error by trying simplified content.
        
        Args:
            operation: Operation name
            original_content: Original content that failed
            error_message: The error that occurred
            retry_function: Function to call with simplified content
            attempt_number: Current attempt number
            
        Returns:
            Dict with recovery result
        """
        # Log the error
        error_record = self.log_error(
            operation=operation,
            error_message=error_message,
            original_content=original_content,
            attempt_number=attempt_number
        )
        
        # Check if we can retry
        if not self.can_retry(operation):
            logger.error("Max retry attempts reached for %s", operation)
            return {
                "success": False,
                "error": f"Max retry attempts ({self.max_retries}) reached",
                "operation": operation
            }
        
        # Get simplified version
        simplified_data = self.get_simplified_version(original_content)
        simplified_content = simplified_data["simplified"]
        
        # Update error record
        error_record.simplified_content = simplified_content
        
        logger.info("Attempting recovery with simplified content for %s", operation)
        
        # Try the retry function
        try:
            result = retry_function(simplified_content)
            
            if result.get("success"):
                # Recovery successful
                error_record.recovered = True
                error_record.recovery_method = "simplified_content"
                self._write_error_log(error_record)
                
                logger.info("Recovery successful for %s", operation)
                return {
                    "success": True,
                    "recovered": True,
                    "recovery_method": "simplified_content",
                    "original_content": original_content,
                    "simplified_content": simplified_content,
                    "result": result
                }
            else:
                # Retry failed
                logger.warning("Recovery attempt failed for %s", operation)
                return {
                    "success": False,
                    "error": result.get("error", "Recovery failed"),
                    "attempted_recovery": True
                }
                
        except Exception as e:
            logger.error("Recovery attempt raised exception: %s", str(e))
            return {
                "success": False,
                "error": str(e),
                "attempted_recovery": True
            }
    
    def get_error_summary(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a summary of errors from the log.
        
        Args:
            operation: Optional operation name to filter
            
        Returns:
            Dict with error summary
        """
        if not self.log_path.exists():
            return {"error": "No error log found"}
        
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count errors by type
            error_types = {}
            operations = {}
            total_errors = 0
            recovered_count = 0
            
            for line in content.split('\n'):
                if line.startswith('ERROR TYPE:'):
                    error_type = line.split(':')[1].strip()
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                elif line.startswith('OPERATION:'):
                    op = line.split(':')[1].strip()
                    operations[op] = operations.get(op, 0) + 1
                elif line.startswith('TIMESTAMP:'):
                    total_errors += 1
                elif line.startswith('RECOVERED: True'):
                    recovered_count += 1
            
            return {
                "total_errors": total_errors,
                "recovered_count": recovered_count,
                "recovery_rate": round(recovered_count / total_errors * 100, 1) if total_errors > 0 else 0,
                "by_type": error_types,
                "by_operation": operations,
                "log_path": str(self.log_path)
            }
            
        except Exception as e:
            logger.error("Failed to read error log: %s", str(e))
            return {"error": str(e)}
    
    def clear_error_count(self, operation: str) -> None:
        """
        Clear error count for an operation (e.g., after successful recovery).
        
        Args:
            operation: Operation name
        """
        if operation in self.error_counts:
            del self.error_counts[operation]
            logger.info("Cleared error count for %s", operation)
    
    def reset_all_counts(self) -> None:
        """
        Reset all error counts.
        """
        self.error_counts.clear()
        self.last_error_time.clear()
        logger.info("Reset all error counts")


# Convenience functions
def log_error(operation: str, error_message: str, content: str = "") -> ErrorRecord:
    """Quick function to log an error."""
    recovery = ErrorRecovery()
    return recovery.log_error(operation, error_message, content)


def can_retry(operation: str) -> bool:
    """Quick function to check if retry is allowed."""
    recovery = ErrorRecovery()
    return recovery.can_retry(operation)


def get_simplified_content(content: str) -> Dict[str, Any]:
    """Quick function to get simplified content."""
    recovery = ErrorRecovery()
    return recovery.get_simplified_version(content)


if __name__ == "__main__":
    # Test the Error Recovery system
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Error Recovery...")
    recovery = ErrorRecovery()
    
    # Test error logging
    print("\n1. Testing error logging...")
    error = recovery.log_error(
        operation="twitter_post",
        error_message="Rate limit exceeded. Try again in 15 minutes.",
        original_content="This is a test post with #hashtags and @mentions https://example.com",
        attempt_number=1
    )
    print(f"Error logged: {error.error_type.value}")
    
    # Test simplified content
    print("\n2. Testing simplified content...")
    simplified = recovery.get_simplified_version(
        "🚀 Check out this amazing post! #AI #Automation @twitter https://example.com/page"
    )
    print(f"Original: {simplified['original']}")
    print(f"Simplified: {simplified['simplified']}")
    print(f"Reduction: {simplified['reduction_percent']}%")
    
    # Test retry check
    print("\n3. Testing retry check...")
    print(f"Can retry twitter_post: {recovery.can_retry('twitter_post')}")
    print(f"Retry delay: {recovery.get_retry_delay('twitter_post')}s")
    
    # Test error summary
    print("\n4. Testing error summary...")
    summary = recovery.get_error_summary()
    print(f"Error summary: {summary}")
    
    print(f"\nError log written to: {recovery.log_path}")
