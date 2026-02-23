# Silver Tier Autonomous Monitor - Setup Guide

## Overview

The Silver Tier Autonomous Monitor runs 24/7 to ensure your Silver Tier automation is always active. It:

- ✅ Auto-starts the Silver Tier watcher
- ✅ Monitors health every 30 seconds
- ✅ Auto-recovers if watcher crashes
- ✅ Sends Discord alerts on failures
- ✅ Sends daily status summaries
- ✅ Logs all events

---

## Quick Start (Choose One Method)

### Method 1: Windows Task Scheduler (Recommended - Auto-start on Boot)

1. **Run as Administrator:**
   ```
   Right-click install_monitor_task.bat → Run as Administrator
   ```

2. **Done!** Monitor will start automatically when Windows boots.

### Method 2: Manual Start (For Testing)

```cmd
cd F:\Tahirah\Hackathon-0\AI_Employee_Vault
python silver_tier_monitor.py
```

### Method 3: Hidden Background Process

Double-click: `start_monitor.bat`

---

## What Happens After Setup

### On Windows Boot
1. Windows Task Scheduler starts `silver_tier_monitor.py`
2. Monitor starts the Silver Tier watcher (`run_silver_tier.py`)
3. Watcher begins monitoring `04_Approved` folder
4. You get a Discord notification: "🟢 Silver Tier watcher started"

### During Operation
- **Every 30 seconds:** Health check performed
- **If watcher crashes:** Auto-restart within 5 seconds
- **Daily at 9 AM:** Status summary sent to Discord
- **On failure:** Immediate Discord alert

### Files Created

| File | Purpose |
|------|---------|
| `logs/silver_tier_monitor.log` | Monitor log file |
| `logs/silver_tier_status.json` | Current status data |

---

## Discord Notifications

You'll receive:

### Startup
```
🚀 Silver Tier Autonomous Monitor started
Time: 2026-02-23 10:00
Monitoring 24/7...
```

### Watcher Started
```
🟢 Silver Tier watcher started
Time: 2026-02-23 10:00
PID: 12345
```

### Health Alert
```
⚠️ Silver Tier Health Issues Detected:

• Watcher process not running

Time: 2026-02-23 10:30
```

### Daily Summary
```
📊 Silver Tier Daily Summary

📅 Date: 2026-02-23
⏱️ Total Uptime: 24.5 hours
📁 Files Processed: 15
🔄 Restart Count: 0
✅ Status: Running
```

---

## Monitoring Commands

### Check if Monitor is Running
```cmd
tasklist | findstr python
```

### Check Windows Task Status
```cmd
schtasks /Query /TN SilverTierMonitor
```

### View Logs
```cmd
type logs\silver_tier_monitor.log
```

### Stop Monitor (Temporary)
```cmd
schtasks /End /TN SilverTierMonitor
```

### Start Monitor (Temporary)
```cmd
schtasks /Run /TN SilverTierMonitor
```

---

## Uninstall

```cmd
schtasks /Delete /TN SilverTierMonitor /F
```

Then delete these files:
- `silver_tier_monitor.py`
- `start_monitor.bat`
- `start_monitor_hidden.vbs`
- `install_monitor_task.bat`

---

## Configuration

Edit `silver_tier_monitor.py` to change:

```python
MONITOR_CONFIG = {
    "health_check_interval": 30,  # Check every 30 seconds
    "max_restart_attempts": 3,     # Max restarts before alerting
    "restart_delay": 5,            # Wait 5 seconds before restart
    "daily_summary_time": "09:00", # Send daily summary at 9 AM
}
```

---

## Troubleshooting

### Monitor Not Starting
1. Check Windows Task Scheduler
2. Ensure Python is in PATH
3. Run `install_monitor_task.bat` as Administrator

### No Discord Notifications
1. Check `discord-mcp-server/.env` has webhook URL
2. Test webhook: `python scripts\tools\mcp_discord_client.py`

### Watcher Keeps Crashing
1. Check `logs\silver_tier_monitor.log` for errors
2. Verify `04_Approved` folder exists
3. Check Discord webhook URL is valid

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Windows Task Scheduler                     │
│              (Starts on boot)                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         silver_tier_monitor.py (24/7 Guardian)          │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Health Check (every 30s)                         │ │
│  │  - Is watcher running?                            │ │
│  │  - Are folders accessible?                        │ │
│  │  - Files processed?                               │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Auto-Recovery                                    │ │
│  │  - Restart watcher if crashed                     │ │
│  │  - Max 3 restarts before alert                    │ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │  Discord Alerts                                   │ │
│  │  - Startup notifications                          │ │
│  │  - Health alerts                                  │ │
│  │  - Daily summaries                                │ │
│  └───────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │ manages
                     ▼
┌─────────────────────────────────────────────────────────┐
│         run_silver_tier.py (File Watcher)               │
│                                                         │
│  - Watches 04_Approved folder                          │
│  - Auto-posts to Discord                               │
│  - Moves files to 05_Done                              │
└─────────────────────────────────────────────────────────┘
```

---

## Hackathon Demo

### Before Demo
1. Ensure monitor is running: `schtasks /Query /TN SilverTierMonitor`
2. Check Discord for startup notification

### During Demo
1. Move a file to `04_Approved`
2. Wait 5 seconds
3. Show Discord notification
4. Explain: "Our autonomous monitor ensures 24/7 operation with auto-recovery"

### For Judges
"This monitor runs as a Windows service, checking health every 30 seconds and auto-recovering from failures. Zero user intervention required."

---

**Status:** ✅ Ready for 24/7 Autonomous Operation
