# Gmail Integration - Quick Start Guide

## ✅ What Was Created

A complete, production-ready Gmail integration system that runs 24/7 in the background.

### Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **Gmail Watcher** | Polls Gmail API every 2 minutes | `gmail_watcher.py` |
| **Gmail Orchestrator** | Manages email processing workflow | `orchestrator.py` |
| **Gmail Monitor** | 24/7 guardian with auto-restart | `gmail_monitor.py` |
| **Email MCP Server** | AI assistant email tools | `email-mcp/` |
| **Gmail Operator Skill** | Email classification & response | `Skills/gmail_operator/SKILL.md` |

---

## 🚀 Quick Setup (5 Steps)

### Step 1: Install Dependencies

```bash
# Python dependencies
cd F:\Tahirah\Hackathon-0\AI_Employee_Vault\gmail-integration
pip install -r requirements.txt

# Node.js dependencies (for MCP server)
cd email-mcp
npm install
```

### Step 2: Get Google Cloud Credentials

1. Go to: https://console.cloud.google.com/apis/credentials
2. Create new project (or select existing)
3. Enable Gmail API
4. Create OAuth2 Client ID (Desktop app)
5. Download JSON → Save as `credentials.json` in `gmail-integration/` folder

### Step 3: Configure .env

Edit `gmail-integration/.env`:

```bash
GMAIL_CLIENT_ID=your_client_id_here
GMAIL_CLIENT_SECRET=your_client_secret_here
DRY_RUN=true
```

### Step 4: Authenticate with Gmail

```bash
cd F:\Tahirah\Hackathon-0\AI_Employee_Vault\gmail-integration
python gmail_oauth.py
```

A browser window will open. Grant permissions.

### Step 5: Start Gmail Integration

**Option A: Manual Start**
```bash
python start_gmail_monitor.bat
```

**Option B: Auto-Start on Windows Boot (Recommended)**

Right-click → Run as Administrator:
```bash
install_gmail_monitor_task.bat
```

---

## 📁 Folder Structure

```
AI_Employee_Vault/
├── gmail-integration/
│   ├── gmail_watcher.py          # Polls Gmail API
│   ├── gmail_oauth.py            # OAuth2 setup
│   ├── orchestrator.py           # Email workflow
│   ├── gmail_monitor.py          # 24/7 guardian
│   ├── start_gmail_monitor.bat   # Quick start
│   ├── install_gmail_monitor_task.bat  # Auto-start
│   └── email-mcp/
│       ├── index.js              # MCP server
│       └── package.json
│
├── 02_Needs_Actions/              # New emails
├── 03_Pending_Approval/           # Awaiting approval
├── 04_Approved/                   # Ready to send
├── 05_Done/                       # Completed
├── 08_Rejected/                   # Rejected
└── Logs/                          # All activity logs
```

---

## 🔄 Email Workflow

```
1. Gmail receives email
       ↓
2. Gmail Watcher detects (every 2 min)
       ↓
3. Creates file in 02_Needs_Actions
       ↓
4. Orchestrator calls AI assistant
       ↓
5. AI classifies intent + drafts response
       ↓
6. Creates approval file in 03_Pending_Approval
       ↓
7. Human reviews:
   - Move to 04_Approved → Send email
   - Move to 08_Rejected → Cancel
       ↓
8. Completed → Move to 05_Done
```

---

## 🧪 Testing (Safe Mode)

With `DRY_RUN=true` (default):

1. **Start Gmail Monitor:**
   ```bash
   python start_gmail_monitor.bat
   ```

2. **Send yourself a test email** with subject "Test"

3. **Wait 2 minutes**

4. **Check `02_Needs_Actions/`** - Email file should appear

5. **Check `Logs/gmail_watcher.log`** - Should show processing

6. **Verify [DRY_RUN] in logs** - No real emails sent

---

## 🎯 Production Mode

**⚠️ WARNING: This sends REAL emails!**

1. **Edit `.env`:**
   ```
   DRY_RUN=false
   ```

2. **Ensure approval workflow is working:**
   - Review files in `03_Pending_Approval/`
   - Only approve after careful review

3. **Restart Gmail Monitor**

4. **Monitor logs closely**

---

## 📊 Monitoring Commands

### Check if Running
```bash
tasklist | findstr python
```

### View Logs
```bash
powershell -Command "Get-Content Logs\gmail_watcher.log -Tail 50"
```

### Check Windows Task Status
```bash
schtasks /Query /TN GmailIntegrationMonitor
```

### Stop Monitor
```bash
schtasks /End /TN GmailIntegrationMonitor
```

---

## 🔒 Security Features

| Feature | Status |
|---------|--------|
| OAuth2 Authentication | ✅ |
| DRY_RUN Mode | ✅ (default: true) |
| Rate Limiting | ✅ (10 emails/hour) |
| Email Validation | ✅ |
| Approval Workflow | ✅ Required |
| Persistent Logging | ✅ JSON logs |

---

## 🛠 Troubleshooting

### "No valid credentials found"
**Fix:** Run `python gmail_oauth.py` again

### "Rate limit reached"
**Fix:** Wait 1 hour or increase `GMAIL_MAX_EMAILS_PER_HOUR` in `.env`

### Watcher not detecting emails
**Fix:**
1. Check `credentials.json` exists
2. Verify Gmail API enabled
3. Check logs for errors

### MCP Server not responding
**Fix:**
```bash
cd gmail-integration\email-mcp
npm install
```

---

## 📋 Files Created

| File | Purpose |
|------|---------|
| `gmail_watcher.py` | Gmail API polling |
| `gmail_oauth.py` | OAuth2 authentication |
| `orchestrator.py` | Email workflow management |
| `gmail_monitor.py` | 24/7 guardian with auto-restart |
| `email-mcp/index.js` | MCP server for AI assistants |
| `email-mcp/package.json` | Node.js dependencies |
| `requirements.txt` | Python dependencies |
| `.env.example` | Configuration template |
| `SKILL.md` | Gmail operator skill definition |
| `start_gmail_monitor.bat` | Quick start script |
| `install_gmail_monitor_task.bat` | Windows Task installer |
| `README.md` | Full documentation |

---

## ✅ Verification Checklist

Before production use:

- [ ] OAuth2 authentication completed
- [ ] Test email received in `02_Needs_Actions/`
- [ ] AI assistant classification working
- [ ] Approval files created
- [ ] Can move files between folders
- [ ] MCP server responds
- [ ] Logs show all actions
- [ ] Rate limiting configured
- [ ] DRY_RUN mode tested

---

**Status:** ✅ Ready for Silver-Tier Gmail Integration

**Documentation:** See `README.md` for full details.

**Support:** Check `Logs/` folder for error messages.
