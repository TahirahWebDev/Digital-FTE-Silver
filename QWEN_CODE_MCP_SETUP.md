# Qwen Code MCP Setup Guide

## The Silver Tier MCP Requirement

**You should be able to tell Qwen:**
> "Send a Discord message saying 'Build complete!'"

**And Qwen should automatically post to Discord** using the MCP tool - no Python scripts to run manually.

---

## Step 1: Find Qwen Code's MCP Config Location

Qwen Code stores MCP configuration in one of these locations:

### Windows:
```
%APPDATA%\Qwen\mcp.json
```
Which is typically:
```
C:\Users\IBRAHIM QURESHI\AppData\Roaming\Qwen\mcp.json
```

### Or project-level:
```
F:\Tahirah\Hackathon-0\AI_Employee_Vault\.qwen\mcp.json
```

---

## Step 2: Add the Discord MCP Server

### Option A: Global Config (Recommended)

1. Press `Win + R`
2. Type: `%APPDATA%\Qwen\mcp.json`
3. Press Enter
4. If file doesn't exist, create it

**Add this configuration:**

```json
{
  "mcpServers": {
    "discord": {
      "command": "node",
      "args": [
        "F:\\Tahirah\\Hackathon-0\\AI_Employee_Vault\\discord-mcp-server\\index.js"
      ],
      "cwd": "F:\\Tahirah\\Hackathon-0\\AI_Employee_Vault\\discord-mcp-server"
    }
  }
}
```

### Option B: Project-Level Config

1. Create folder: `F:\Tahirah\Hackathon-0\AI_Employee_Vault\.qwen\`
2. Create file: `mcp.json`
3. Add the same configuration as above

---

## Step 3: Restart Qwen Code

After adding the MCP config:
1. Close Qwen Code completely
2. Reopen Qwen Code
3. The MCP server will now be available as a tool

---

## Step 4: Test It

### Tell Qwen:
```
Send a Discord message saying "MCP test from Qwen!"
```

### Expected Behavior:
Qwen should:
1. Recognize it has access to the `send_discord_message` tool
2. Call the tool with your message
3. You should see the message appear in your Discord channel

---

## Step 5: Verify MCP is Working

### Check Available Tools
Ask Qwen:
```
What tools do you have available?
```

You should see something like:
```
I have access to the following tools:
- send_discord_message: Send a message to Discord via webhook
```

---

## Troubleshooting

### "I don't see the MCP tool"
1. Verify the MCP server runs:
   ```cmd
   cd F:\Tahirah\Hackathon-0\AI_Employee_Vault\discord-mcp-server
   npm start
   ```
   Should show: "Discord MCP Server running on stdio"

2. Check that `node` is in your PATH:
   ```cmd
   node --version
   ```

3. Verify npm packages are installed:
   ```cmd
   cd F:\Tahirah\Hackathon-0\AI_Employee_Vault\discord-mcp-server
   npm install
   ```

4. Restart Qwen Code after any changes

### "Path not found" error
Make sure the paths in `mcp.json` are correct:
- `args[0]` should point to `index.js`
- `cwd` should point to the `discord-mcp-server` folder

### "DISCORD_WEBHOOK_URL not found"
Check that `.env` file exists in `discord-mcp-server` folder with:
```
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

---

## Example Usage Scenarios

### 1. Simple Notification
**You:** "Notify Discord that the build is complete"

**Qwen:** [Calls `send_discord_message` with message="🎉 Build complete!"]

### 2. Approval Request
**You:** "Ask the team on Discord to review the new feature"

**Qwen:** [Calls `send_discord_message` with message="⚠️ Review Request: New feature ready for testing. Please review in the 03_Pending_Approval folder."]

### 3. Status Update
**You:** "Post a status update to Discord"

**Qwen:** [Calls `send_discord_message` with message="📊 Status: 5 files processed today. All systems operational."]

### 4. Error Alert
**You:** "Alert Discord about the processing error"

**Qwen:** [Calls `send_discord_message` with message="❌ Error: Failed to process file.txt - missing required fields"]

---

## MCP Server Architecture

```
┌──────────────┐
│   You        │
│   (User)     │
└──────┬───────┘
       │ tells
       ▼
┌──────────────┐
│   Qwen Code  │──────────────┐
│   (AI)       │              │
└──────┬───────┘              │
       │ calls tool           │
       ▼                      │
┌─────────────────────────────┴──┐
│  MCP Server                    │
│  (discord-mcp-server/index.js) │
│  - Exposes send_discord_message│
└──────────────┬─────────────────┘
               │ sends to
               ▼
      ┌─────────────────┐
      │  Discord API    │
      │  Webhook        │
      └─────────────────┘
```

---

## Hackathon Demo Script

### Setup (Before Judge Arrives)
1. Ensure MCP config is added to Qwen Code
2. Restart Qwen Code
3. Verify tool is available

### Demo Flow
1. **Tell the judge:** "Our AI employee can post to Discord directly via MCP"

2. **Type to Qwen:** 
   ```
   Send a Discord message saying "Hackathon demo in progress!"
   ```

3. **Show Discord:** Message appears automatically

4. **Explain:** "This uses the Model Context Protocol (MCP) to expose Discord messaging as an AI tool. No Python scripts needed - the AI calls the tool directly."

---

## Configuration File Reference

### Complete mcp.json Example

```json
{
  "mcpServers": {
    "discord": {
      "command": "node",
      "args": [
        "F:\\Tahirah\\Hackathon-0\\AI_Employee_Vault\\discord-mcp-server\\index.js"
      ],
      "cwd": "F:\\Tahirah\\Hackathon-0\\AI_Employee_Vault\\discord-mcp-server",
      "env": {}
    }
  }
}
```

### Field Explanations

| Field | Purpose |
|-------|---------|
| `command` | The executable to run (`node`) |
| `args[0]` | Path to the MCP server script |
| `cwd` | Working directory (where `.env` is loaded from) |
| `env` | Additional environment variables (optional) |

---

## Quick Commands

### Test MCP Server Directly
```cmd
cd F:\Tahirah\Hackathon-0\AI_Employee_Vault\discord-mcp-server
npm start
```

### Check if Node is Available
```cmd
node --version
```

### Verify .env File
```cmd
type F:\Tahirah\Hackathon-0\AI_Employee_Vault\discord-mcp-server\.env
```

---

## Next Steps After Setup

1. ✅ Add MCP config to Qwen Code
2. ✅ Restart Qwen Code
3. ✅ Test with a simple message
4. ✅ Demo for hackathon judges

---

**Status:** Ready for Silver Tier MCP Demo!
