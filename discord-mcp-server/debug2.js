const sdk = require('@modelcontextprotocol/sdk');
console.log('Main SDK exports:', Object.keys(sdk));

// Try different import approaches
try {
  const server = require('@modelcontextprotocol/sdk/server');
  console.log('Server exports:', Object.keys(server));
} catch (e) {
  console.log('Server import failed:', e.message);
}

try {
  const mcp = require('@modelcontextprotocol/sdk/dist/cjs/server/mcp');
  console.log('MCP exports:', Object.keys(mcp));
} catch (e) {
  console.log('MCP import failed:', e.message);
}