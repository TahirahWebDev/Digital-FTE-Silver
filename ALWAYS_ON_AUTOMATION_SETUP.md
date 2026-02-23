# Silver Tier - Always-On Automation Setup

## The Requirement

> "The automation should always work, not only after running the file"

This means the **file watcher must run continuously** in the background, not just when you manually execute a script.

---

## Solution: Run the Watcher as a Background Process

Your Silver Tier automation consists of:
1. **File Watcher** (`run_silver_tier.py`) - Monitors `04_Approved` folder
2. **MCP Server** (`discord-mcp-server/`) - Allows AI assistants to call Discord tools

Both need to run continuously.

---

## Option 1: Quick Start (Manual Background Process)

### Windows Batch File (Created)

Double-click to start:
```
start_silver_automation.bat
```

This opens a command window that stays open and runs the watcher.

**Pros:** Simple, easy to monitor
**Cons:** Window must stay open, stops if you close it

---

## Option 2: Windows Task Scheduler (Recommended for Hackathon)

Run automatically when you log in:

### Step 1: Open Task Scheduler
1. Press `Win + R`
2. Type `taskschd.msc`
3. Press Enter

### Step 2: Create Basic Task
1. Click **"Create Basic Task"** in the right panel
2. Name: `AI Employee Silver Tier`
3. Trigger: **"When I log on"**
4. Action: **"Start a program"**
5. Program/script: `python`
6. Arguments: `run_silver_tier.py`
7. Start in: `F:\Tahirah\Hackathon-0\AI_Employee_Vault`

### Step 3: Configure for Background Running
1. After creation, right-click the task → **Properties**
2. Check **"Run whether user is logged on or not"**
3. Check **"Run with highest privileges"**
4. Conditions tab: Uncheck "Stop if computer switches to battery"

### Step 4: Test
Right-click task → **Run**

Check `05_Done` folder after moving a file to `04_Approved`.

---

## Option 3: NSSM (Windows Service - Most Reliable)

Install as a proper Windows service:

### Step 1: Download NSSM
```
https://nssm.cc/download
```

### Step 2: Install Service
```cmd
cd C:\path\to\nssm
nssm install SilverTierAutomation
```

### Step 3: Configure Service
In the NSSM GUI:
- **Path:** `C:\Python314\python.exe` (your Python path)
- **Arguments:** `run_silver_tier.py`
- **Startup directory:** `F:\Tahirah\Hackathon-0\AI_Employee_Vault`

### Step 4: Start Service
```cmd
nssm start SilverTierAutomation
```

Or use Services app (`services.msc`) → Find "SilverTierAutomation" → Start

---

## Option 4: Startup Folder (Simplest)

### Create Shortcut
1. Right-click `run_silver_tier.py` → **Create shortcut**
2. Move shortcut to: `shell:startup` (paste in File Explorer address bar)
3. Shortcut now runs when you log in

### Hide Console Window (Optional)
Create a VBScript wrapper:

**File:** `start_silver_hidden.vbs`
```vbscript
Set objShell = CreateObject("WScript.Shell")
objShell.Run "python F:\Tahirah\Hackathon-0\AI_Employee_Vault\run_silver_tier.py", 0, False
```

Put the VBScript in startup instead.

---

## Verify Automation is Working

### Test Flow:
1. Ensure watcher is running (check Task Manager for `python.exe`)
2. Create a test file: `F:\Tahirah\Hackathon-0\AI_Employee_Vault\04_Approved\test.md`
3. Content: `# Test Post\nAutomation is working!`
4. Wait 5-10 seconds
5. Check:
   - Discord channel → Should see the message
   - `05_Done` folder → File should be moved there

---

## MCP Server (For AI Assistants)

The MCP server is **separate** from the watcher. It allows AI assistants to call Discord tools directly.

### Run MCP Server (if using AI assistant integration):
```bash
cd discord-mcp-server
npm start
```

**Note:** The MCP server is for AI assistant tool calls. The Python watcher is for automatic file-based posting. Both can run simultaneously.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   ALWAYS-RUNNING PROCESSES                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐         ┌───────────────────────┐ │
│  │  Python Watcher     │         │   MCP Server (Node)   │ │
│  │  (run_silver_tier)  │         │   (discord-mcp-srv)   │ │
│  │                     │         │                       │ │
│  │  Watches:           │         │   For AI assistants   │ │
│  │  - 04_Approved/     │         │   to call tools       │ │
│  │  - Auto-posts       │         │                       │ │
│  └─────────┬───────────┘         └───────────┬───────────┘ │
│            │                                 │             │
│            │         ┌───────────────────────┘             │
│            ▼         ▼                                     │
│            ┌──────────────────┐                           │
│            │   Discord API    │                           │
│            │   Webhook        │                           │
│            └──────────────────┘                           │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

---

## Hackathon Demo Setup

For your hackathon demonstration:

### Before Demo:
1. **Start the watcher** (Option 2 or 3 recommended)
2. **Verify it's running** (Task Manager → python.exe)
3. **Test once** with a sample file

### During Demo:
1. Move a file to `04_Approved`
2. Wait 5 seconds
3. Show Discord message appearing automatically
4. Show file moved to `05_Done`

### For Judges:
Explain: "The watcher runs as a background service, so it's always monitoring for new content. This is the Silver Tier automation requirement."

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Watcher not starting | Check Python path in task/service |
| Files not posting | Check `04_Approved` folder permissions |
| Discord not receiving | Verify webhook URL in `.env` |
| Service won't start | Run as Administrator |

---

## Quick Commands

### Check if watcher is running:
```cmd
tasklist | findstr python
```

### Start manually:
```cmd
cd F:\Tahirah\Hackathon-0\AI_Employee_Vault
python run_silver_tier.py
```

### Stop manually:
Press `Ctrl+C` in the console window

### Restart Windows service (if using NSSM):
```cmd
nssm restart SilverTierAutomation
```
