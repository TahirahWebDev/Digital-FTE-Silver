"""
Business Auditor - Generates Business Report after every post.

This module tracks business metrics and updates the Business_Report.md file
in the 00_CEO_Briefings folder after each task completion.

Features:
- Tracks total posts made to all platforms
- Tracks total revenue logged in Xero
- Updates report after every post
- Maintains historical data

Usage:
    from scripts.tools.auditor import BusinessAuditor

    auditor = BusinessAuditor()
    auditor.update_report(
        task_name="Social Media Post",
        platforms=["discord"],
        xero_amount=1.00,
        xero_success=True
    )
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import json

logger = logging.getLogger(__name__)

from scripts.config import CEO_BRIEFINGS_PATH, AUDIT_LOG_PATH, VAULT_PATH


class BusinessAuditor:
    """
    Generates and maintains Business Report after every post.

    Tracks:
    - Total posts made (Discord)
    - Total revenue logged in Xero
    - Task completion history
    """
    
    def __init__(self):
        """
        Initialize the Business Auditor.
        """
        self.briefings_folder = CEO_BRIEFINGS_PATH
        self.audit_folder = AUDIT_LOG_PATH
        self.report_path = self.briefings_folder / "Business_Report.md"
        self.gold_status_path = self.audit_folder / "GOLD_STATUS.md"
        
        # Ensure folders exist
        self.briefings_folder.mkdir(parents=True, exist_ok=True)
        self.audit_folder.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize metrics
        self.metrics = self._load_metrics()
        
        logger.info("Business Auditor initialized")
    
    def _load_metrics(self) -> Dict[str, Any]:
        """
        Load existing metrics from report or initialize new.
        
        Returns:
            Dict with current metrics
        """
        default_metrics = {
            "total_posts": 0,
            "total_revenue": 0.00,
            "posts_by_platform": {
                "discord": 0
            },
            "xero_entries": 0,
            "failed_posts": 0,
            "tasks_completed": [],
            "last_updated": datetime.now().isoformat(),
            "created": datetime.now().isoformat()
        }
        
        if not self.report_path.exists():
            logger.info("Creating new Business Report")
            return default_metrics
        
        try:
            # Try to read existing metrics from report frontmatter
            with open(self.report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for JSON metrics block in the report
            if "<!-- METRICS_START -->" in content and "<!-- METRICS_END -->" in content:
                start = content.find("<!-- METRICS_START -->") + len("<!-- METRICS_START -->")
                end = content.find("<!-- METRICS_END -->")
                metrics_json = content[start:end].strip()
                metrics = json.loads(metrics_json)
                logger.info("Loaded existing metrics from Business Report")
                return metrics
            
        except Exception as e:
            logger.warning("Could not load existing metrics: %s", str(e))
        
        return default_metrics
    
    def _save_metrics(self) -> bool:
        """
        Save current metrics to report file.
        
        Returns:
            True if successfully saved
        """
        self.metrics["last_updated"] = datetime.now().isoformat()
        
        try:
            # Generate the report content
            content = self._generate_report_content()
            
            # Write to file
            with open(self.report_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("Business Report updated: %s", self.report_path)
            return True
            
        except Exception as e:
            logger.error("Failed to save Business Report: %s", str(e))
            return False
    
    def _generate_report_content(self) -> str:
        """
        Generate the full Business Report markdown content.

        Returns:
            Formatted markdown string
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Calculate success rate (with division by zero protection)
        total_attempts = self.metrics["total_posts"] + self.metrics["failed_posts"]
        if total_attempts > 0:
            success_rate = (self.metrics["total_posts"] / total_attempts) * 100
        else:
            success_rate = 0.0

        # Calculate average per task (with division by zero protection)
        xero_entries = self.metrics.get('xero_entries', 0)
        total_revenue = self.metrics.get('total_revenue', 0.0)
        if xero_entries > 0:
            avg_per_task = total_revenue / xero_entries
        else:
            avg_per_task = 0.0

        content = f"""---
title: "Business Report - Gold Tier Autonomous Agent"
generated: "{now}"
tags: [business-report, gold-tier, automation]
category: executive-summary
---

# 📊 Business Report - Gold Tier Autonomous Agent

**Last Updated:** {now}  
**Report Location:** `{self.report_path}`

---

## 📈 Key Metrics

<!-- METRICS_START -->
```json
{json.dumps(self.metrics, indent=2)}
```
<!-- METRICS_END -->

| Metric | Value |
|--------|-------|
| **Total Posts Made** | {self.metrics['total_posts']} |
| **Total Revenue (Xero)** | ${total_revenue:.2f} |
| **Xero Entries** | {xero_entries} |
| **Success Rate** | {success_rate:.1f}% |

---

## 📱 Posts by Platform

| Platform | Posts |
|----------|-------|
| Discord | {self.metrics['posts_by_platform'].get('discord', 0)} |

---

## 💰 Revenue Summary

- **Total Logged in Xero:** ${total_revenue:.2f}
- **Average per Task:** ${avg_per_task:.2f}
- **Xero Entries Count:** {xero_entries}

---

## 📋 Recent Task History

"""
        
        # Add recent tasks (last 10)
        recent_tasks = self.metrics.get("tasks_completed", [])[-10:]
        
        if recent_tasks:
            content += "| # | Task | Platforms | Revenue | Status |\n"
            content += "|---|------|-----------|---------|--------|\n"
            
            for i, task in enumerate(recent_tasks, 1):
                platforms = ", ".join(task.get("platforms", []))
                revenue = f"${task.get('revenue', 0):.2f}"
                status = "✅" if task.get("success", False) else "❌"
                content += f"| {i} | {task.get('name', 'Unknown')} | {platforms} | {revenue} | {status} |\n"
        else:
            content += "*No tasks completed yet.*\n"
        
        content += f"""
---

## ⚠️ Error Status

"""
        
        # Check for recent errors
        if self.gold_status_path.exists():
            try:
                with open(self.gold_status_path, 'r', encoding='utf-8') as f:
                    error_content = f.read()
                
                # Extract recent errors (last 500 chars)
                recent_errors = error_content[-500:] if len(error_content) > 500 else error_content
                content += f"```\n{recent_errors}\n```\n"
            except:
                content += "*No recent errors.*\n"
        else:
            content += "*No errors recorded.*\n"
        
        content += f"""
---

## 🤖 Gold Tier Status

**Autonomous Agent:** Active
**Watching Folder:** `04_Approved`
**Action:** Posts to Discord, Logs to Xero
**Error Handling:** Files move to `07_Reviewing` on failure

---

*Report automatically generated by Gold Tier Autonomous Business Agent*
"""
        
        return content
    
    def update_report(
        self,
        task_name: str,
        platforms: Optional[List[str]] = None,
        xero_amount: float = 0.00,
        xero_success: bool = False,
        post_success: bool = True,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update the Business Report after a post attempt.

        Args:
            task_name: Name of the completed task
            platforms: List of platforms posted to (discord)
            xero_amount: Amount logged to Xero
            xero_success: Whether Xero logging succeeded
            post_success: Whether posting succeeded
            error_message: Optional error message if failed

        Returns:
            True if report updated successfully
        """
        # Update metrics
        if post_success:
            self.metrics["total_posts"] += 1
            
            # Update platform counts
            if platforms:
                for platform in platforms:
                    if platform in self.metrics["posts_by_platform"]:
                        self.metrics["posts_by_platform"][platform] += 1
        else:
            self.metrics["failed_posts"] += 1
        
        # Update Xero metrics
        if xero_success:
            self.metrics["xero_entries"] += 1
            self.metrics["total_revenue"] += xero_amount
        
        # Add to task history
        self.metrics["tasks_completed"].append({
            "name": task_name,
            "timestamp": datetime.now().isoformat(),
            "platforms": platforms or [],
            "revenue": xero_amount if xero_success else 0,
            "xero_logged": xero_success,
            "success": post_success,
            "error": error_message
        })
        
        # Keep only last 100 tasks in memory
        if len(self.metrics["tasks_completed"]) > 100:
            self.metrics["tasks_completed"] = self.metrics["tasks_completed"][-100:]
        
        # Save metrics to report
        return self._save_metrics()
    
    def log_error(
        self,
        operation: str,
        error_message: str,
        task_name: str,
        destination: str = "07_Reviewing"
    ) -> bool:
        """
        Log an error to GOLD_STATUS.md.

        Args:
            operation: Operation that failed (xero)
            error_message: The error message
            task_name: Name of the task
            destination: Where file was moved

        Returns:
            True if logged successfully
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        error_entry = f"""
---
**Timestamp:** {timestamp}
**Operation:** {operation}
**Task:** {task_name}
**Error:** {error_message}
**Action Taken:** File moved to {destination}
---
"""
        
        try:
            # Append to GOLD_STATUS.md
            with open(self.gold_status_path, 'a', encoding='utf-8') as f:
                f.write(error_entry)
            
            logger.info("Error logged to GOLD_STATUS.md")
            return True
            
        except Exception as e:
            logger.error("Failed to log error: %s", str(e))
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current metrics.
        
        Returns:
            Dict with key metrics
        """
        return {
            "total_posts": self.metrics["total_posts"],
            "total_revenue": self.metrics["total_revenue"],
            "xero_entries": self.metrics["xero_entries"],
            "failed_posts": self.metrics["failed_posts"],
            "last_updated": self.metrics["last_updated"]
        }


# Convenience function
def update_business_report(
    task_name: str,
    platforms: Optional[List[str]] = None,
    xero_amount: float = 0.00,
    xero_success: bool = False,
    post_success: bool = True,
    error_message: Optional[str] = None
) -> bool:
    """
    Quick function to update the Business Report.
    
    Args:
        task_name: Name of the completed task
        platforms: List of platforms posted to
        xero_amount: Amount logged to Xero
        xero_success: Whether Xero logging succeeded
        post_success: Whether posting succeeded
        error_message: Optional error message
        
    Returns:
        True if report updated successfully
    """
    auditor = BusinessAuditor()
    return auditor.update_report(
        task_name=task_name,
        platforms=platforms,
        xero_amount=xero_amount,
        xero_success=xero_success,
        post_success=post_success,
        error_message=error_message
    )


if __name__ == "__main__":
    # Test the Business Auditor
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Business Auditor...")
    auditor = BusinessAuditor()
    
    # Simulate a successful post
    print("\n1. Simulating successful post...")
    auditor.update_report(
        task_name="Test Social Media Post",
        platforms=["discord"],
        xero_amount=1.00,
        xero_success=True,
        post_success=True
    )

    # Simulate a failed post
    print("\n2. Simulating failed post...")
    auditor.update_report(
        task_name="Failed Post",
        platforms=["discord"],
        xero_amount=0.00,
        xero_success=False,
        post_success=False,
        error_message="Discord webhook error: 404 Not Found"
    )

    # Log an error
    print("\n3. Logging error...")
    auditor.log_error(
        operation="xero",
        error_message="401 Unauthorized - Token expired",
        task_name="Failed Post"
    )
    
    # Get summary
    print("\n4. Getting summary...")
    summary = auditor.get_summary()
    print(f"Summary: {summary}")
    
    print(f"\nBusiness Report saved to: {auditor.report_path}")
    print(f"Error log saved to: {auditor.gold_status_path}")
