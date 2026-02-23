#!/usr/bin/env node
/**
 * Discord MCP Server
 * Exposes send_discord_message tool for AI assistants
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

// Load .env from current directory
const __dirname = dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: join(__dirname, ".env") });

const DISCORD_WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL;

if (!DISCORD_WEBHOOK_URL) {
  console.error("ERROR: DISCORD_WEBHOOK_URL not found in .env file");
  process.exit(1);
}

// Create MCP server
const server = new Server(
  {
    name: "discord-mcp-server",
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
        name: "send_discord_message",
        description:
          "Send a message to Discord via webhook. Use this to notify users about events, approvals, or status updates.",
        inputSchema: {
          type: "object",
          properties: {
            message: {
              type: "string",
              description: "The message content to send to Discord",
            },
          },
          required: ["message"],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "send_discord_message") {
    const message = args?.message;

    if (!message) {
      return {
        content: [
          {
            type: "text",
            text: "Error: 'message' argument is required",
          },
        ],
        isError: true,
      };
    }

    try {
      // Send to Discord webhook
      const response = await fetch(DISCORD_WEBHOOK_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          content: message,
        }),
      });

      if (response.ok || response.status === 204) {
        return {
          content: [
            {
              type: "text",
              text: `✅ Message sent to Discord successfully`,
            },
          ],
        };
      } else {
        const errorText = await response.text();
        return {
          content: [
            {
              type: "text",
              text: `❌ Discord API error: ${response.status} - ${errorText}`,
            },
          ],
          isError: true,
        };
      }
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `❌ Error sending message: ${error.message}`,
          },
        ],
        isError: true,
      };
    }
  }

  return {
    content: [
      {
        type: "text",
        text: `Unknown tool: ${name}`,
      },
    ],
    isError: true,
  };
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Discord MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
