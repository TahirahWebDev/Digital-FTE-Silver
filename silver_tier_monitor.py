#!/usr/bin/env python3
"""
Silver Tier Autonomous Monitor - 24/7 Guardian

This script continuously monitors and manages the Silver Tier automation system.
It automatically starts, stops, restarts, and monitors the Silver Tier watcher.

Features:
- Auto-starts Silver Tier watcher if not running
- Monitors health every 30 seconds
- Auto-recovers if watcher crashes
- Logs all events to Discord and file
- Sends alerts on failures
- Runs 24/7 without user intervention

Usage:
    python silver_tier_monitor.py
    
Or set up to run at Windows startup.
"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import threading
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.config import VAULT_PATH, APPROVED_PATH, DONE_PATH
from scripts.tools.mcp_discord_client import send_discord_message

# ============================================================================
# Configuration
# ============================================================================

MONITOR_CONFIG = {
    "health_check_interval": 30,  # Check every 30 seconds
    "max_restart_attempts": 3,     # Max restarts before alerting
    "restart_delay": 5,            # Wait 5 seconds before restart
    "log_file": "logs/silver_tier_monitor.log",
    "status_file": "logs/silver_tier_status.json",
    "alert_on_failure": True,
    "daily_summary_time": "09:00",  # Send daily summary at 9 AM
}

# Paths
SILVER_TIER_SCRIPT = PROJECT_ROOT / "run_silver_tier.py"
LOG_FOLDER = PROJECT_ROOT / "logs"
STATUS_FILE = PROJECT_ROOT / MONITOR_CONFIG["status_file"]
LOG_FILE = PROJECT_ROOT / MONITOR_CONFIG["log_file"]

# Ensure log folder exists
LOG_FOLDER.mkdir(parents=True, exist_ok=True)

# Use config paths
APPROVED_FOLDER = APPROVED_PATH
DONE_FOLDER = DONE_PATH

# ============================================================================
# Logging Setup
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# Status Tracking
# ============================================================================

class SilverTierStatus:
    """Tracks and persists Silver Tier status."""
    
    def __init__(self, status_file: Path):
        self.status_file = status_file
        self.status = self._load_status()
    
    def _load_status(self) -> dict:
        """Load status from file or create new."""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load status file: {e}")
        
        return {
            "watcher_running": False,
            "watcher_pid": None,
            "last_health_check": None,
            "last_restart": None,
            "restart_count": 0,
            "total_uptime_hours": 0,
            "start_time": None,
            "errors": [],
            "files_processed": 0,
            "last_file_processed": None,
            "status": "initializing"
        }
    
    def save(self):
        """Save current status to file."""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.status, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save status: {e}")
    
    def update(self, **kwargs):
        """Update status fields."""
        for key, value in kwargs.items():
            self.status[key] = value
        self.status["last_health_check"] = datetime.now().isoformat()
        self.save()

# ============================================================================
# Silver Tier Process Manager
# ============================================================================

class SilverTierManager:
    """Manages the Silver Tier watcher process."""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.restart_attempts = 0
        self.last_restart_time: Optional[datetime] = None
        self.start_time: Optional[datetime] = None
    
    def start_watcher(self) -> bool:
        """Start the Silver Tier watcher."""
        try:
            logger.info("Starting Silver Tier watcher...")
            
            # Start as subprocess - don't capture output to avoid blocking
            self.process = subprocess.Popen(
                [sys.executable, str(SILVER_TIER_SCRIPT)],
                cwd=str(PROJECT_ROOT),
                # Don't capture output - let it go to null to avoid blocking
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            self.start_time = datetime.now()
            self.restart_attempts = 0
            
            logger.info(f"Silver Tier watcher started (PID: {self.process.pid})")
            
            # Send Discord notification
            send_discord_message(
                f"🟢 Silver Tier watcher started\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"PID: {self.process.pid}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Silver Tier watcher: {e}")
            send_discord_message(f"❌ Failed to start Silver Tier watcher\nError: {str(e)}")
            return False
    
    def stop_watcher(self):
        """Stop the Silver Tier watcher."""
        if self.process:
            try:
                logger.info("Stopping Silver Tier watcher...")
                self.process.terminate()
                self.process.wait(timeout=10)
                logger.info("Silver Tier watcher stopped")
                
                send_discord_message("🔴 Silver Tier watcher stopped by monitor")
                
            except Exception as e:
                logger.error(f"Error stopping watcher: {e}")
                try:
                    self.process.kill()
                except:
                    pass
            finally:
                self.process = None
                self.start_time = None
    
    def is_running(self) -> bool:
        """Check if watcher is running by checking process list."""
        if self.process is None:
            return False
        
        # Check if process is still alive using poll
        if self.process.poll() is None:
            return True
        
        # Fallback: check if any python.exe is running (watcher might have detached)
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/NH'],
                capture_output=True,
                text=True,
                timeout=5
            )
            # If we see multiple python processes, watcher is likely running
            python_count = result.stdout.count('python.exe')
            return python_count >= 2  # Monitor + Watcher
        except:
            return False
    
    def restart_watcher(self) -> bool:
        """Restart the watcher."""
        now = datetime.now()
        
        # Check if we've exceeded max restart attempts
        if self.restart_attempts >= MONITOR_CONFIG["max_restart_attempts"]:
            # Check if enough time has passed since last restart
            if self.last_restart_time:
                time_since_restart = (now - self.last_restart_time).total_seconds()
                if time_since_restart < 300:  # 5 minutes
                    logger.error("Max restart attempts reached. Not restarting.")
                    send_discord_message(
                        f"⚠️ Silver Tier watcher failed {MONITOR_CONFIG['max_restart_attempts']} times.\n"
                        f"Manual intervention may be required."
                    )
                    return False
        
        logger.info(f"Restarting Silver Tier watcher (attempt {self.restart_attempts + 1})")
        
        # Stop if running
        if self.is_running():
            self.stop_watcher()
        
        # Wait before restart
        time.sleep(MONITOR_CONFIG["restart_delay"])
        
        # Start
        success = self.start_watcher()
        
        if success:
            self.restart_attempts = 0
            self.last_restart_time = now
        else:
            self.restart_attempts += 1
            self.last_restart_time = now
        
        return success

# ============================================================================
# Health Monitor
# ============================================================================

class HealthMonitor:
    """Monitors Silver Tier health and file processing."""
    
    def __init__(self, manager: SilverTierManager, status: SilverTierStatus):
        self.manager = manager
        self.status = status
        self.last_file_count = 0
        self.last_check_time = datetime.now()
    
    def check_health(self) -> dict:
        """Perform health check."""
        health = {
            "timestamp": datetime.now().isoformat(),
            "watcher_running": self.manager.is_running(),
            "approved_folder_exists": APPROVED_FOLDER.exists(),
            "done_folder_exists": DONE_FOLDER.exists(),
            "files_in_approved": 0,
            "files_processed_since_last_check": 0,
            "uptime_hours": 0,
            "issues": []
        }
        
        # Check folders
        if not health["approved_folder_exists"]:
            health["issues"].append("04_Approved folder missing")
            logger.warning("04_Approved folder missing!")
        
        if not health["done_folder_exists"]:
            health["issues"].append("05_Done folder missing")
            logger.warning("05_Done folder missing!")
        
        # Count files in Approved folder
        if health["approved_folder_exists"]:
            try:
                files = list(APPROVED_FOLDER.glob("*.md")) + list(APPROVED_FOLDER.glob("*.txt"))
                health["files_in_approved"] = len(files)
            except Exception as e:
                logger.error(f"Error counting files in Approved: {e}")
        
        # Calculate files processed
        current_count = self.status.status.get("files_processed", 0)
        health["files_processed_since_last_check"] = current_count - self.last_file_count
        self.last_file_count = current_count
        
        # Calculate uptime
        if self.manager.start_time:
            health["uptime_hours"] = (datetime.now() - self.manager.start_time).total_seconds() / 3600
        
        # Check for issues
        if not health["watcher_running"]:
            health["issues"].append("Watcher process not running")
        
        return health
    
    def send_alert(self, issues: list):
        """Send alert for health issues."""
        if not issues:
            return
        
        message = "⚠️ Silver Tier Health Issues Detected:\n\n"
        for issue in issues:
            message += f"• {issue}\n"
        
        message += f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        send_discord_message(message)
        logger.warning(f"Health issues: {issues}")

# ============================================================================
# Daily Summary Reporter
# ============================================================================

class DailyReporter:
    """Sends daily status summaries."""
    
    def __init__(self, status: SilverTierStatus):
        self.status = status
        self.last_report_date = None
    
    def check_and_send(self):
        """Check if daily report should be sent."""
        now = datetime.now()
        today = now.date()
        
        # Check if it's time for daily report
        target_time = datetime.strptime(
            f"{today.strftime('%Y-%m-%d')} {MONITOR_CONFIG['daily_summary_time']}",
            "%Y-%m-%d %H:%M"
        ).time()
        
        if now.time().hour == target_time.hour and now.time().minute >= target_time.minute:
            if self.last_report_date != today:
                self.send_summary()
                self.last_report_date = today
    
    def send_summary(self):
        """Send daily summary to Discord."""
        status = self.status.status
        
        # Calculate stats
        uptime = status.get("total_uptime_hours", 0)
        files_processed = status.get("files_processed", 0)
        restart_count = status.get("restart_count", 0)
        
        summary = f"""📊 Silver Tier Daily Summary

📅 Date: {datetime.now().strftime('%Y-%m-%d')}
⏱️ Total Uptime: {uptime:.1f} hours
📁 Files Processed: {files_processed}
🔄 Restart Count: {restart_count}
✅ Status: {'Running' if status.get('watcher_running') else 'Stopped'}

Last file: {status.get('last_file_processed', 'None')}

_Silver Tier Autonomous Monitor_"""

        send_discord_message(summary)
        logger.info("Daily summary sent")

# ============================================================================
# Main Monitor Service
# ============================================================================

class SilverTierMonitor:
    """Main autonomous monitor service."""
    
    def __init__(self):
        self.status = SilverTierStatus(STATUS_FILE)
        self.manager = SilverTierManager()
        self.health_monitor = HealthMonitor(self.manager, self.status)
        self.daily_reporter = DailyReporter(self.status)
        self.running = False
    
    def start(self):
        """Start the monitor service."""
        logger.info("=" * 60)
        logger.info("Silver Tier Autonomous Monitor Starting...")
        logger.info("=" * 60)
        
        self.running = True
        
        # Update status
        self.status.update(
            status="running",
            start_time=datetime.now().isoformat()
        )
        
        # Send startup notification
        send_discord_message(
            "🚀 Silver Tier Autonomous Monitor started\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            "Monitoring 24/7..."
        )
        
        # Start the watcher if not already running
        if not self.manager.is_running():
            logger.info("Watcher not running, starting now...")
            self.manager.start_watcher()
        
        # Main monitoring loop
        try:
            while self.running:
                self.monitoring_cycle()
                time.sleep(MONITOR_CONFIG["health_check_interval"])
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user")
            self.stop()
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            self.stop()
    
    def monitoring_cycle(self):
        """One cycle of monitoring."""
        logger.debug("Running health check...")
        
        # Check health
        health = self.health_monitor.check_health()
        
        # Update status
        self.status.update(
            watcher_running=health["watcher_running"],
            watcher_pid=self.manager.process.pid if self.manager.process else None,
            files_processed=self.status.status.get("files_processed", 0) + health["files_processed_since_last_check"],
            total_uptime_hours=health["uptime_hours"]
        )
        
        # Handle issues
        if health["issues"]:
            self.health_monitor.send_alert(health["issues"])
            
            # Auto-recover if watcher not running
            if not health["watcher_running"]:
                logger.warning("Watcher not running, attempting restart...")
                self.manager.restart_watcher()
        
        # Check for daily report
        self.daily_reporter.check_and_send()
        
        # Log status
        logger.info(
            f"Health OK | Watcher: {'✓' if health['watcher_running'] else '✗'} | "
            f"Files in Approved: {health['files_in_approved']} | "
            f"Uptime: {health['uptime_hours']:.1f}h"
        )
    
    def stop(self):
        """Stop the monitor service."""
        logger.info("Stopping Silver Tier Monitor...")
        self.running = False
        self.manager.stop_watcher()
        
        self.status.update(
            status="stopped",
            watcher_running=False
        )
        
        send_discord_message("🛑 Silver Tier Autonomous Monitor stopped")
        logger.info("Monitor stopped")

# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Silver Tier Autonomous Monitor")
    print("=" * 60)
    print("Starting 24/7 monitoring...")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    monitor = SilverTierMonitor()
    monitor.start()
