#!/usr/bin/env python3
"""
Gmail Integration Monitor - 24/7 Guardian

Monitors and manages both Gmail Watcher and Orchestrator.
Auto-starts, monitors health, and recovers from failures.
Runs 24/7 in background without user intervention.

Features:
- Auto-starts Gmail Watcher and Orchestrator
- Monitors health every 30 seconds
- Auto-recovers if processes crash
- Logs all events to Discord and file
- Sends alerts on failures
- Runs 24/7 without user intervention
"""

import os
import sys
import time
import subprocess
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.tools.mcp_discord_client import send_discord_message

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Configuration
MONITOR_CONFIG = {
    "health_check_interval": 30,
    "max_restart_attempts": 3,
    "restart_delay": 5,
    "log_file": "Logs/gmail_monitor.log",
    "status_file": "Logs/gmail_monitor_status.json",
    "alert_on_failure": True,
}

# Paths
GMAIL_WATCHER_SCRIPT = PROJECT_ROOT / "gmail-integration" / "gmail_watcher.py"
ORCHESTRATOR_SCRIPT = PROJECT_ROOT / "gmail-integration" / "orchestrator.py"
LOG_FOLDER = PROJECT_ROOT / "Logs"
STATUS_FILE = PROJECT_ROOT / MONITOR_CONFIG["status_file"]
LOG_FILE = PROJECT_ROOT / MONITOR_CONFIG["log_file"]

# Ensure log folder exists
LOG_FOLDER.mkdir(parents=True, exist_ok=True)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GmailProcessManager:
    """Manages Gmail Watcher and Orchestrator processes."""
    
    def __init__(self):
        self.watcher_process: Optional[subprocess.Popen] = None
        self.orchestrator_process: Optional[subprocess.Popen] = None
        self.restart_attempts = {"watcher": 0, "orchestrator": 0}
        self.last_restart_time = {"watcher": None, "orchestrator": None}
        self.start_time = {"watcher": None, "orchestrator": None}
    
    def start_watcher(self) -> bool:
        """Start Gmail Watcher."""
        try:
            logger.info("Starting Gmail Watcher...")
            
            self.watcher_process = subprocess.Popen(
                [sys.executable, str(GMAIL_WATCHER_SCRIPT)],
                cwd=str(GMAIL_WATCHER_SCRIPT.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            self.start_time["watcher"] = datetime.now()
            self.restart_attempts["watcher"] = 0
            
            logger.info(f"Gmail Watcher started (PID: {self.watcher_process.pid})")
            
            send_discord_message(
                f"🟢 Gmail Watcher started\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"PID: {self.watcher_process.pid}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Gmail Watcher: {e}")
            send_discord_message(f"❌ Failed to start Gmail Watcher\nError: {str(e)}")
            return False
    
    def start_orchestrator(self) -> bool:
        """Start Orchestrator."""
        try:
            logger.info("Starting Gmail Orchestrator...")
            
            self.orchestrator_process = subprocess.Popen(
                [sys.executable, str(ORCHESTRATOR_SCRIPT)],
                cwd=str(ORCHESTRATOR_SCRIPT.parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            self.start_time["orchestrator"] = datetime.now()
            self.restart_attempts["orchestrator"] = 0
            
            logger.info(f"Gmail Orchestrator started (PID: {self.orchestrator_process.pid})")
            
            send_discord_message(
                f"🟢 Gmail Orchestrator started\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"PID: {self.orchestrator_process.pid}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Gmail Orchestrator: {e}")
            send_discord_message(f"❌ Failed to start Gmail Orchestrator\nError: {str(e)}")
            return False
    
    def stop_process(self, process: Optional[subprocess.Popen], name: str):
        """Stop a process."""
        if process:
            try:
                logger.info(f"Stopping {name}...")
                process.terminate()
                process.wait(timeout=10)
                logger.info(f"{name} stopped")
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")
                try:
                    process.kill()
                except:
                    pass
    
    def is_watcher_running(self) -> bool:
        """Check if watcher is running."""
        if self.watcher_process is None:
            return False
        return self.watcher_process.poll() is None
    
    def is_orchestrator_running(self) -> bool:
        """Check if orchestrator is running."""
        if self.orchestrator_process is None:
            return False
        return self.orchestrator_process.poll() is None
    
    def restart_watcher(self) -> bool:
        """Restart watcher."""
        now = datetime.now()
        
        if self.restart_attempts["watcher"] >= MONITOR_CONFIG["max_restart_attempts"]:
            if self.last_restart_time["watcher"]:
                time_since_restart = (now - self.last_restart_time["watcher"]).total_seconds()
                if time_since_restart < 300:
                    logger.error("Max watcher restart attempts reached.")
                    send_discord_message(
                        f"⚠️ Gmail Watcher failed {MONITOR_CONFIG['max_restart_attempts']} times.\n"
                        f"Manual intervention may be required."
                    )
                    return False
        
        logger.info(f"Restarting Gmail Watcher (attempt {self.restart_attempts['watcher'] + 1})")
        
        if self.is_watcher_running():
            self.stop_process(self.watcher_process, "Gmail Watcher")
        
        time.sleep(MONITOR_CONFIG["restart_delay"])
        
        success = self.start_watcher()
        
        if success:
            self.restart_attempts["watcher"] = 0
        else:
            self.restart_attempts["watcher"] += 1
        
        self.last_restart_time["watcher"] = now
        return success
    
    def restart_orchestrator(self) -> bool:
        """Restart orchestrator."""
        now = datetime.now()
        
        if self.restart_attempts["orchestrator"] >= MONITOR_CONFIG["max_restart_attempts"]:
            if self.last_restart_time["orchestrator"]:
                time_since_restart = (now - self.last_restart_time["orchestrator"]).total_seconds()
                if time_since_restart < 300:
                    logger.error("Max orchestrator restart attempts reached.")
                    send_discord_message(
                        f"⚠️ Gmail Orchestrator failed {MONITOR_CONFIG['max_restart_attempts']} times.\n"
                        f"Manual intervention may be required."
                    )
                    return False
        
        logger.info(f"Restarting Gmail Orchestrator (attempt {self.restart_attempts['orchestrator'] + 1})")
        
        if self.is_orchestrator_running():
            self.stop_process(self.orchestrator_process, "Gmail Orchestrator")
        
        time.sleep(MONITOR_CONFIG["restart_delay"])
        
        success = self.start_orchestrator()
        
        if success:
            self.restart_attempts["orchestrator"] = 0
        else:
            self.restart_attempts["orchestrator"] += 1
        
        self.last_restart_time["orchestrator"] = now
        return success
    
    def stop_all(self):
        """Stop all processes."""
        logger.info("Stopping all Gmail processes...")
        self.stop_process(self.watcher_process, "Gmail Watcher")
        self.stop_process(self.orchestrator_process, "Gmail Orchestrator")
        send_discord_message("🛑 Gmail Integration Monitor stopped")


class GmailMonitor:
    """Main monitor service for Gmail integration."""
    
    def __init__(self):
        self.manager = GmailProcessManager()
        self.running = False
        self.status = {
            "watcher_running": False,
            "orchestrator_running": False,
            "start_time": None,
            "total_uptime_hours": 0,
            "restart_count": {"watcher": 0, "orchestrator": 0},
            "last_health_check": None
        }
    
    def start(self):
        """Start the monitor service."""
        logger.info("=" * 60)
        logger.info("Gmail Integration Monitor Starting...")
        logger.info("=" * 60)
        
        self.running = True
        self.status["start_time"] = datetime.now().isoformat()
        
        send_discord_message(
            "🚀 Gmail Integration Monitor started\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            "Monitoring Gmail 24/7..."
        )
        
        # Start processes
        if not self.manager.is_watcher_running():
            logger.info("Watcher not running, starting now...")
            self.manager.start_watcher()
        
        if not self.manager.is_orchestrator_running():
            logger.info("Orchestrator not running, starting now...")
            self.manager.start_orchestrator()
        
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
        
        # Check watcher health
        watcher_running = self.manager.is_watcher_running()
        if not watcher_running:
            logger.warning("Gmail Watcher not running, attempting restart...")
            if self.manager.restart_watcher():
                self.status["restart_count"]["watcher"] += 1
        
        # Check orchestrator health
        orchestrator_running = self.manager.is_orchestrator_running()
        if not orchestrator_running:
            logger.warning("Gmail Orchestrator not running, attempting restart...")
            if self.manager.restart_orchestrator():
                self.status["restart_count"]["orchestrator"] += 1
        
        # Update status
        self.status["watcher_running"] = watcher_running
        self.status["orchestrator_running"] = orchestrator_running
        self.status["last_health_check"] = datetime.now().isoformat()
        
        # Calculate uptime
        if self.status["start_time"]:
            start = datetime.fromisoformat(self.status["start_time"])
            self.status["total_uptime_hours"] = (datetime.now() - start).total_seconds() / 3600
        
        # Log status
        logger.info(
            f"Health OK | Watcher: {'✓' if watcher_running else '✗'} | "
            f"Orchestrator: {'✓' if orchestrator_running else '✗'} | "
            f"Uptime: {self.status['total_uptime_hours']:.1f}h"
        )
    
    def stop(self):
        """Stop the monitor service."""
        logger.info("Stopping Gmail Monitor...")
        self.running = False
        self.manager.stop_all()
        logger.info("Monitor stopped")


def main():
    """Entry point."""
    print("=" * 60)
    print("Gmail Integration Monitor")
    print("=" * 60)
    print("Starting 24/7 monitoring...")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    monitor = GmailMonitor()
    monitor.start()


if __name__ == '__main__':
    main()
