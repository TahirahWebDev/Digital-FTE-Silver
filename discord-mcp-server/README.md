# Discord MCP Server

Minimal MCP server that exposes a `send_discord_message` tool for AI assistants to send Discord notifications.

## Folder Structure

```
discord-mcp-server/
├── .env                  # DISCORD_WEBHOOK_URL (already configured)
├── index.js              # MCP server code
├── package.json          # Dependencies
└── README.md             # This file
```

## Quick Setup

### 1. Install Dependencies

```bash
cd discord-mcp-server
npm install
```

### 2. Verify .env File

Your `.env` already contains the webhook URL:
```
DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
```

### 3. Test the Server (Optional)

```bash
npm start
```

The server runs on stdio (standard input/output) for MCP communication.

---

## Register in Claude Code (mcp.json)

Add this to your Claude Code MCP config:

**Location:** `C:\Users\IBRAHIM QURESHI\.claude\mcp.json` (or project-level `.claude/mcp.json`)

```json
{
  "mcpServers": {
    "discord": {
      "command": "node",
      "args": ["F:\\Tahirah\\Hackathon-0\\AI_Employee_Vault\\discord-mcp-server\\index.js"],
      "cwd": "F:\\Tahirah\\Hackathon-0\\AI_Employee_Vault\\discord-mcp-server"
    }
  }
}
```

**For Qwen Code or other MCP clients**, use the same configuration format in your respective MCP config file.

---

## Usage Example

Once registered, Claude can call the tool like this:

### Example 1: Simple Notification
```
Please send a Discord message: "🚀 Silver Tier MCP integration complete!"
```

### Example 2: Approval Request
```
Call send_discord_message with:
{
  "message": "⚠️ Approval Required: New file created in vault. Please review."
}
```

### Example 3: In a Workflow
```python
# Your existing Python workflow can now trigger via MCP
# Instead of direct webhook call, Claude calls the MCP tool

# Before (Python script):
# requests.post(WEBHOOK_URL, json={"content": message})

# After (Claude via MCP):
# Claude calls send_discord_message(message="...")
```

---

## Tool Schema

**Name:** `send_discord_message`

**Parameters:**
| Parameter | Type   | Required | Description                      |
|-----------|--------|----------|----------------------------------|
| message   | string | Yes      | The message content to send      |

**Response:**
- `✅ Message sent to Discord successfully` - on success
- `❌ Discord API error: ...` - on Discord API failure
- `❌ Error sending message: ...` - on network error

---

## Testing

### Manual Test with curl (verify webhook works):
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"content":"Test from curl"}' \
  "YOUR_WEBHOOK_URL"
```

### MCP Tool Test:
Once registered, ask Claude:
```
Send a test message to Discord saying "MCP server test successful"
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `DISCORD_WEBHOOK_URL not found` | Check `.env` file exists in discord-mcp-server folder |
| `npm install` fails | Ensure Node.js 18+ is installed |
| Messages not appearing in Discord | Verify webhook URL is valid and not revoked |
| MCP server not connecting | Check mcp.json paths are absolute and correct |

---

## Silver Tier Compliance

This MCP server satisfies the Silver Tier requirement by:
- ✅ Exposing functionality as an MCP tool (not just a script)
- ✅ Using the official `@modelcontextprotocol/sdk`
- ✅ Following MCP tool schema conventions
- ✅ Allowing AI assistants to call Discord messaging as a tool
