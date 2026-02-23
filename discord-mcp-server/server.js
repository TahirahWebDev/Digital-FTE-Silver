const express = require('express');
const { McpServer } = require('@modelcontextprotocol/sdk/dist/cjs/server/mcp'); // Correct import
const { z } = require('zod');
const { createMcpExpressApp } = require('@modelcontextprotocol/sdk/dist/cjs/server/express');

// Create MCP server with implementation details
const mcpServer = new McpServer({
  name: 'discord-notifications',
  version: '1.0.0'
});

// Register the send_discord_message tool using the registerTool method
mcpServer.registerTool('send_discord_message', {
  title: 'Send Discord Message', // Display name for UI
  description: 'Send a message to Discord via webhook',
  inputSchema: {
    message: z.string().describe('The message to send to Discord')
  }
}, async ({ message }) => {
  const webhookUrl = process.env.DISCORD_WEBHOOK_URL;

  if (!webhookUrl) {
    throw new Error("DISCORD_WEBHOOK_URL environment variable is not set");
  }

  try {
    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content: message
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to send message to Discord: ${response.status} ${response.statusText}`);
    }

    return {
      content: [
        {
          type: 'text',
          text: 'Message sent to Discord successfully'
        }
      ]
    };
  } catch (error) {
    console.error('Error sending message to Discord:', error);
    return {
      content: [
        {
          type: 'text',
          text: `Failed to send message to Discord: ${error.message}`
        }
      ],
      isError: true
    };
  }
});

// Create Express app with MCP configuration
const app = createMcpExpressApp();

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Set up MCP transport
const transports = {};

// MCP POST endpoint
app.post('/mcp', async (req, res) => {
  const sessionId = req.headers['mcp-session-id'];

  if (sessionId && transports[sessionId]) {
    // Reuse existing transport
    const transport = transports[sessionId];
    await transport.handleRequest(req, res, req.body);
  } else if (!sessionId && req.body.method === 'initialize') {
    // New initialization request
    const { InMemoryEventStore } = require('@modelcontextprotocol/sdk/server');
    const { StreamableHTTPServerTransport } = require('@modelcontextprotocol/sdk/server/streamableHttp');

    const eventStore = new InMemoryEventStore();
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => require('crypto').randomUUID(),
      eventStore,
      onsessioninitialized: (sessionId) => {
        transports[sessionId] = transport;
      }
    });

    // Clean up transport when closed
    transport.onclose = () => {
      const sid = transport.sessionId;
      if (sid && transports[sid]) {
        delete transports[sid];
      }
    };

    // Connect the transport to the MCP server
    await mcpServer.connect(transport);
    await transport.handleRequest(req, res, req.body);
  } else {
    // Invalid request
    res.status(400).json({
      jsonrpc: '2.0',
      error: {
        code: -32000,
        message: 'Bad Request: No valid session ID provided'
      },
      id: null
    });
  }
});

// Handle GET requests for SSE streams
app.get('/mcp', async (req, res) => {
  const sessionId = req.headers['mcp-session-id'];
  if (!sessionId || !transports[sessionId]) {
    res.status(400).send('Invalid or missing session ID');
    return;
  }

  const transport = transports[sessionId];
  await transport.handleRequest(req, res);
});

// Handle DELETE requests for session termination
app.delete('/mcp', async (req, res) => {
  const sessionId = req.headers['mcp-session-id'];
  if (!sessionId || !transports[sessionId]) {
    res.status(400).send('Invalid or missing session ID');
    return;
  }

  const transport = transports[sessionId];
  await transport.handleRequest(req, res);
});

// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Discord MCP Server running on port ${PORT}`);
  console.log(`MCP endpoint available at http://localhost:${PORT}/mcp`);
});