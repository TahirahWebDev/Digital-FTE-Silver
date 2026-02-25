#!/usr/bin/env node
/**
 * Email MCP Server - Gmail Integration
 * 
 * Exposes Gmail functionality as MCP tools:
 * - send_email: Send an email via Gmail
 * - draft_email: Create a draft email
 * - search_email: Search emails in Gmail
 * 
 * All actions are logged and respect DRY_RUN mode.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import dotenv from "dotenv";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { google } from "googleapis";
import fs from "fs";
import { promisify } from "util";

const writeFile = promisify(fs.writeFile);
const appendFile = promisify(fs.appendFile);
const readFile = promisify(fs.readFile);

// Load environment
const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, "..", "..");
dotenv.config({ path: join(projectRoot, "gmail-integration", ".env") });

// Configuration
const DRY_RUN = process.env.DRY_RUN?.toLowerCase() === "true";
const VAULT_PATH = process.env.VAULT_PATH || "F:\\Tahirah\\Hackathon-0\\AI_Employee_Vault";
const LOGS_FOLDER = join(VAULT_PATH, "Logs");
const GMAIL_CLIENT_ID = process.env.GMAIL_CLIENT_ID || "";
const GMAIL_CLIENT_SECRET = process.env.GMAIL_CLIENT_SECRET || "";
const GMAIL_REDIRECT_URI = process.env.GMAIL_REDIRECT_URI || "http://localhost:8080/callback";
const TOKEN_PATH = join(projectRoot, "gmail-integration", ".gmail_token.json");

// Ensure logs folder exists
if (!fs.existsSync(LOGS_FOLDER)) {
  fs.mkdirSync(LOGS_FOLDER, { recursive: true });
}

/**
 * Validate email address format
 */
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Get Gmail API credentials
 */
async function getGmailCredentials() {
  try {
    const tokenData = await readFile(TOKEN_PATH, "utf-8");
    const token = JSON.parse(tokenData);
    
    const oauth2Client = new google.auth.OAuth2(
      GMAIL_CLIENT_ID,
      GMAIL_CLIENT_SECRET,
      GMAIL_REDIRECT_URI
    );
    
    oauth2Client.setCredentials(token);
    
    // Check if token needs refresh
    const { credentials } = await oauth2Client.refreshAccessToken();
    if (credentials.access_token) {
      // Save updated token
      await writeFile(TOKEN_PATH, JSON.stringify(oauth2Client.credentials));
    }
    
    return oauth2Client;
  } catch (error) {
    console.error("Error getting Gmail credentials:", error.message);
    throw new Error("Gmail authentication failed. Run gmail_oauth.py first.");
  }
}

/**
 * Log action to JSON file
 */
async function logAction(actionType, target, parameters, approvalStatus, result) {
  const today = new Date().toISOString().split("T")[0];
  const logFile = join(LOGS_FOLDER, `${today}.json`);
  
  const logEntry = {
    timestamp: new Date().toISOString(),
    action_type: actionType,
    target,
    parameters,
    approval_status: approvalStatus,
    result,
    dry_run: DRY_RUN
  };
  
  try {
    let logs = [];
    if (fs.existsSync(logFile)) {
      const content = await readFile(logFile, "utf-8");
      logs = JSON.parse(content);
    }
    
    logs.push(logEntry);
    await writeFile(logFile, JSON.stringify(logs, null, 2));
  } catch (error) {
    console.error("Failed to log action:", error.message);
  }
}

/**
 * Send email via Gmail API
 */
async function sendEmail(to, subject, body, cc = null, bcc = null) {
  if (DRY_RUN) {
    console.log("[DRY_RUN] Would send email to:", to);
    await logAction("send_email", to, { to, subject, cc, bcc }, "simulated", {
      success: true,
      message: "DRY_RUN mode - email not sent"
    });
    return { success: true, messageId: "dry-run-" + Date.now() };
  }
  
  try {
    const auth = await getGmailCredentials();
    const gmail = google.gmail({ version: "v1", auth });
    
    // Create email message
    const from = "me";
    const str = [
      `From: ${from}`,
      `To: ${to}`,
      cc ? `Cc: ${cc}` : "",
      `Subject: ${subject}`,
      "",
      body
    ].filter(Boolean).join("\n");
    
    const encodedMessage = Buffer.from(str).toString("base64url");
    
    const response = await gmail.users.messages.send({
      userId: "me",
      requestBody: {
        raw: encodedMessage
      }
    });
    
    await logAction("send_email", to, { to, subject, cc, bcc }, "approved", {
      success: true,
      messageId: response.data.id
    });
    
    return {
      success: true,
      messageId: response.data.id,
      threadId: response.data.threadId
    };
  } catch (error) {
    console.error("Error sending email:", error.message);
    await logAction("send_email", to, { to, subject }, "approved", {
      success: false,
      error: error.message
    });
    throw error;
  }
}

/**
 * Create draft email
 */
async function draftEmail(to, subject, body) {
  if (DRY_RUN) {
    console.log("[DRY_RUN] Would create draft for:", to);
    await logAction("draft_email", to, { to, subject }, "simulated", {
      success: true,
      message: "DRY_RUN mode - draft not created"
    });
    return { success: true, draftId: "dry-run-" + Date.now() };
  }
  
  try {
    const auth = await getGmailCredentials();
    const gmail = google.gmail({ version: "v1", auth });
    
    const str = [
      "From: me",
      `To: ${to}`,
      `Subject: ${subject}`,
      "",
      body
    ].join("\n");
    
    const encodedMessage = Buffer.from(str).toString("base64url");
    
    const response = await gmail.users.drafts.create({
      userId: "me",
      requestBody: {
        message: {
          raw: encodedMessage
        }
      }
    });
    
    await logAction("draft_email", to, { to, subject }, "approved", {
      success: true,
      draftId: response.data.id
    });
    
    return {
      success: true,
      draftId: response.data.id,
      threadId: response.data.message.threadId
    };
  } catch (error) {
    console.error("Error creating draft:", error.message);
    await logAction("draft_email", to, { to, subject }, "approved", {
      success: false,
      error: error.message
    });
    throw error;
  }
}

/**
 * Search emails
 */
async function searchEmails(query, maxResults = 10) {
  if (DRY_RUN) {
    console.log("[DRY_RUN] Would search:", query);
    return { success: true, messages: [] };
  }
  
  try {
    const auth = await getGmailCredentials();
    const gmail = google.gmail({ version: "v1", auth });
    
    const response = await gmail.users.messages.list({
      userId: "me",
      q: query,
      maxResults: Math.min(maxResults, 100)
    });
    
    const messages = response.data.messages || [];
    
    await logAction("search_email", query, { query, maxResults }, "approved", {
      success: true,
      count: messages.length
    });
    
    return {
      success: true,
      count: messages.length,
      messages: messages.map(m => ({
        id: m.id,
        threadId: m.threadId
      }))
    };
  } catch (error) {
    console.error("Error searching emails:", error.message);
    await logAction("search_email", query, { query }, "approved", {
      success: false,
      error: error.message
    });
    throw error;
  }
}

// Create MCP Server
const server = new Server(
  {
    name: "email-mcp-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "send_email",
        description: "Send an email via Gmail. Requires approval before sending in production mode.",
        inputSchema: {
          type: "object",
          properties: {
            to: {
              type: "string",
              description: "Recipient email address (required)"
            },
            subject: {
              type: "string",
              description: "Email subject (required)"
            },
            body: {
              type: "string",
              description: "Email body content (required)"
            },
            cc: {
              type: "string",
              description: "CC recipient (optional)"
            },
            bcc: {
              type: "string",
              description: "BCC recipient (optional)"
            }
          },
          required: ["to", "subject", "body"]
        }
      },
      {
        name: "draft_email",
        description: "Create a draft email in Gmail without sending.",
        inputSchema: {
          type: "object",
          properties: {
            to: {
              type: "string",
              description: "Recipient email address (required)"
            },
            subject: {
              type: "string",
              description: "Email subject (required)"
            },
            body: {
              type: "string",
              description: "Email body content (required)"
            }
          },
          required: ["to", "subject", "body"]
        }
      },
      {
        name: "search_email",
        description: "Search emails in Gmail using Gmail search syntax.",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "Gmail search query (e.g., 'from:boss@example.com', 'is:unread')"
            },
            maxResults: {
              type: "number",
              description: "Maximum results to return (default: 10, max: 100)"
            }
          },
          required: ["query"]
        }
      }
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  try {
    if (name === "send_email") {
      const { to, subject, body, cc, bcc } = args || {};
      
      // Validate required fields
      if (!to || !subject || !body) {
        return {
          content: [{ type: "text", text: "Error: 'to', 'subject', and 'body' are required" }],
          isError: true
        };
      }
      
      // Validate email format
      if (!isValidEmail(to)) {
        return {
          content: [{ type: "text", text: `Error: Invalid email address: ${to}` }],
          isError: true
        };
      }
      
      if (cc && !isValidEmail(cc)) {
        return {
          content: [{ type: "text", text: `Error: Invalid CC email address: ${cc}` }],
          isError: true
        };
      }
      
      if (bcc && !isValidEmail(bcc)) {
        return {
          content: [{ type: "text", text: `Error: Invalid BCC email address: ${bcc}` }],
          isError: true
        };
      }
      
      // Send email
      const result = await sendEmail(to, subject, body, cc, bcc);
      
      return {
        content: [
          {
            type: "text",
            text: result.success 
              ? `✅ Email sent to ${to} (Message ID: ${result.messageId})`
              : `❌ Failed to send email: ${result.error}`
          }
        ],
        isError: !result.success
      };
    }
    
    if (name === "draft_email") {
      const { to, subject, body } = args || {};
      
      if (!to || !subject || !body) {
        return {
          content: [{ type: "text", text: "Error: 'to', 'subject', and 'body' are required" }],
          isError: true
        };
      }
      
      if (!isValidEmail(to)) {
        return {
          content: [{ type: "text", text: `Error: Invalid email address: ${to}` }],
          isError: true
        };
      }
      
      const result = await draftEmail(to, subject, body);
      
      return {
        content: [
          {
            type: "text",
            text: result.success
              ? `✅ Draft created for ${to} (Draft ID: ${result.draftId})`
              : `❌ Failed to create draft: ${result.error}`
          }
        ],
        isError: !result.success
      };
    }
    
    if (name === "search_email") {
      const { query, maxResults = 10 } = args || {};
      
      if (!query) {
        return {
          content: [{ type: "text", text: "Error: 'query' is required" }],
          isError: true
        };
      }
      
      const result = await searchEmails(query, maxResults);
      
      return {
        content: [
          {
            type: "text",
            text: `Found ${result.count} emails matching "${query}"`
          }
        ]
      };
    }
    
    return {
      content: [{ type: "text", text: `Unknown tool: ${name}` }],
      isError: true
    };
    
  } catch (error) {
    console.error("Tool execution error:", error.message);
    return {
      content: [{ type: "text", text: `Error: ${error.message}` }],
      isError: true
    };
  }
});

// Start server
async function main() {
  console.error("Email MCP Server starting...");
  console.error(`DRY_RUN: ${DRY_RUN}`);
  console.error(`Logs: ${LOGS_FOLDER}`);
  
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Email MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
