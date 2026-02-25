# Gmail Integration - Complete Setup Guide

**Silver-Tier AI Employee Gmail System**

Autonomous Gmail integration with:
- 24/7 background email monitoring
- AI-powered email classification
- Human-in-the-loop approval workflow
- MCP server for AI assistant integration
- Auto-restart and error recovery

---

## 📁 Folder Structure

```
AI_Employee_Vault/
├── gmail-integration/
│   ├── gmail_watcher.py          # Main Gmail watcher
│   ├── gmail_oauth.py            # OAuth2 token generator
│   ├── orchestrator.py           # Email processing orchestrator
│   ├── requirements.txt          # Python dependencies
│   ├── .env                      # Configuration (create from .env.example)
│   ├── start_gmail_watcher.bat   # Quick start script
│   ├── start_gmail_watcher_hidden.vbs  # Hidden runner
│   ├── install_gmail_watcher_task.bat  # Windows Task installer
│   └── email-mcp/
│       ├── index.js              # Email MCP server
│       └── package.json          # Node.js dependencies
│
├── 01_Inbox/                      # Raw Gmail inbox (optional)
├── 02_Needs_Actions/              # New emails needing action
├── 03_Pending_Approval/           # Emails awaiting approval
├── 04_Approved/                   # Approved emails ready to send
├── 05_Done/                       # Completed emails
├── 08_Rejected/                   # Rejected emails
├── Logs/                          # All activity logs
└── Skills/gmail_operator/
    └── SKILL.md                   # Gmail operator skill definition
```

---

## 🚀 Installation Steps

### Step 1: Install Python Dependencies

```bash
cd F:\Tahirah\Hackathon-0\AI_Employee_Vault\gmail-integration
pip install -r requirements.txt
```

### Step 2: Install Node.js Dependencies (for MCP Server)

```bash
cd F:\Tahirah\Hackathon-0\AI_Employee_Vault\gmail-integration\email-mcp
npm install
```

### Step 3: Set Up Google Cloud Project

1. **Go to Google Cloud Console:**
   https://console.cloud.google.com/apis/credentials

2. **Create a new project** (or select existing)

3. **Enable Gmail API:**
   - Go to "Library"
   - Search for "Gmail API"
   - Click "Enable"

4. **Create OAuth2 Credentials:**
   - Go to "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: **Desktop app**
   - Download the JSON file
   - Save as `credentials.json` in `gmail-integration/` folder

5. **Configure OAuth consent screen:**
   - Go to "OAuth consent screen"
   - Add your email as test user
   - Add scopes: `gmail.readonly`, `gmail.send`, `gmail.compose`

### Step 4: Configure Environment

1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and add your credentials:
   ```
   GMAIL_CLIENT_ID=your_client_id_from_credentials.json
   GMAIL_CLIENT_SECRET=your_client_secret_from_credentials.json
   GMAIL_REDIRECT_URI=http://localhost:8080/callback
   DRY_RUN=true
   ```

### Step 5: Authenticate with Gmail

Run the OAuth2 setup script:

```bash
cd F:\Tahirah\Hackathon-0\AI_Employee_Vault\gmail-integration
python gmail_oauth.py
```

A browser window will open. Grant permissions. Token will be saved to `.gmail_token.json`.

---

## ▶️ How to Run

### Option 1: Quick Start (Manual)

```bash
# Start Gmail Watcher (runs in foreground)
cd gmail-integration
python gmail_watcher.py

# In another terminal, start Orchestrator
python orchestrator.py
```

### Option 2: Background Mode (Recommended)

**Double-click:**
```
gmail-integration\start_gmail_watcher.bat
```

This starts Gmail Watcher hidden in the background.

### Option 3: Auto-Start on Windows Boot (Best for 24/7)

**Right-click → Run as Administrator:**
```
gmail-integration\install_gmail_watcher_task.bat
```

This installs Gmail Watcher as a Windows Task that starts automatically when you log in.

---

## 🧪 How to Test Safely

### Test with DRY_RUN Enabled (Default)

With `DRY_RUN=true` in `.env`:

1. **No emails will actually be sent**
2. **All actions are logged**
3. **Safe for testing the full workflow**

### Test Workflow

1. **Start Gmail Watcher:**
   ```bash
   python gmail_watcher.py
   ```

2. **Send yourself a test email** with subject containing "test"

3. **Wait 2 minutes** (poll interval)

4. **Check `/02_Needs_Actions/`** - New email file should appear

5. **Check `Logs/gmail_watcher.log`** - Should show processing

6. **Verify DRY_RUN in logs:**
   ```
   [DRY_RUN] Would send email to: ...
   ```

---

## 🔧 How to Disable DRY_RUN (Production Mode)

**⚠️ WARNING: This will send REAL emails!**

1. **Edit `.env`:**
   ```
   DRY_RUN=false
   ```

2. **Ensure approval workflow is in place:**
   - All emails require approval before sending
   - Review files in `/03_Pending_Approval/`
   - Only move to `/04_Approved/` after review

3. **Restart Gmail Watcher:**
   - Kill existing process
   - Start again with `start_gmail_watcher.bat`

4. **Monitor logs closely:**
   ```bash
   tail -f Logs/gmail_watcher.log
   ```

---

## 📊 Monitoring

### Check Gmail Watcher Status

```bash
# Check if running
tasklist | findstr python

# View logs
type Logs\gmail_watcher.log
```

### Check Windows Task Status

```bash
schtasks /Query /TN GmailWatcher
```

### View Today's Logs

```bash
powershell -Command "Get-Content Logs\gmail_watcher.log -Tail 50"
```

---

## 🔒 Security Features

| Feature | Description |
|---------|-------------|
| **OAuth2 Authentication** | Secure Gmail API access |
| **DRY_RUN Mode** | Test without sending real emails |
| **Rate Limiting** | Max 10 emails/hour (configurable) |
| **Email Validation** | Validates email addresses before sending |
| **Approval Workflow** | No email sent without approval |
| **Persistent Logging** | All actions logged to JSON files |
| **Token Storage** | OAuth tokens stored securely in `.gmail_token.json` |

---

## 🛠 Troubleshooting

### "No valid credentials found"

**Solution:** Run `python gmail_oauth.py` again to refresh token.

### "Rate limit reached"

**Solution:** Wait 1 hour or increase `GMAIL_MAX_EMAILS_PER_HOUR` in `.env`.

### "Gmail API error: invalid_grant"

**Solution:** Delete `.gmail_token.json` and run `gmail_oauth.py` again.

### Watcher not detecting emails

**Solution:**
1. Check `credentials.json` exists
2. Verify Gmail API is enabled
3. Check logs for errors
4. Ensure email is unread and marked as important

### MCP Server not responding

**Solution:**
```bash
cd gmail-integration\email-mcp
npm install
node index.js
```

---

## 📋 Approval Workflow

### For Each Email:

1. **Gmail Watcher** detects new email → Creates file in `/02_Needs_Actions/`

2. **Orchestrator** detects new file → Calls AI assistant

3. **AI Assistant** (using gmail_operator skill):
   - Classifies intent
   - Creates plan in `/Plans/`
   - Drafts response
   - Creates approval file in `/03_Pending_Approval/`

4. **Human Review:**
   - Review draft in `/03_Pending_Approval/`
   - If approved → Move to `/04_Approved/`
   - If rejected → Move to `/08_Rejected/`

5. **Orchestrator** detects approved file → Calls MCP `send_email`

6. **Email sent** → Files moved to `/05_Done/`

---

## 🎯 Configuration Options

Edit `.env` to customize:

| Variable | Default | Description |
|----------|---------|-------------|
| `GMAIL_POLL_INTERVAL` | 120 | Seconds between Gmail checks |
| `GMAIL_MAX_EMAILS_PER_HOUR` | 10 | Rate limit |
| `DRY_RUN` | true | Safe mode (no real emails) |
| `ORCHESTRATOR_POLL_INTERVAL` | 10 | Seconds between folder checks |
| `VAULT_PATH` | (auto) | Path to vault root |

---

## 📝 Log Files

| Log File | Purpose |
|----------|---------|
| `Logs/gmail_watcher.log` | Gmail Watcher activity |
| `Logs/gmail_orchestrator.log` | Orchestrator activity |
| `Logs/gmail_YYYY-MM-DD.json` | Daily email actions |
| `Logs/gmail_orchestrator_YYYY-MM-DD.json` | Daily orchestrator actions |

---

## ✅ Verification Checklist

Before enabling production mode (`DRY_RUN=false`):

- [ ] OAuth2 authentication completed
- [ ] Test email received in `/02_Needs_Actions/`
- [ ] AI assistant classification working
- [ ] Approval files created in `/03_Pending_Approval/`
- [ ] Can move files between folders
- [ ] MCP server responds to test calls
- [ ] Logs show all actions
- [ ] Rate limiting configured
- [ ] Email validation working

---

**Status:** ✅ Ready for Silver-Tier Gmail Integration

**Support:** Check `Logs/` folder for detailed error messages.
