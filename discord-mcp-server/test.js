const axios = require('axios');

async function testServer() {
  try {
    // Test health endpoint
    const healthResponse = await axios.get('http://localhost:3000/health');
    console.log('Health check:', healthResponse.data);

    // Test MCP discovery endpoint
    const mcpResponse = await axios.get('http://localhost:3000/mcp', {
      headers: {
        'Authorization': 'Bearer test-token', // MCP typically uses bearer tokens
        'Content-Type': 'application/json'
      }
    });
    console.log('MCP endpoint status:', mcpResponse.status);
    console.log('MCP response headers:', mcpResponse.headers);

    console.log('Server is running and accessible!');
  } catch (error) {
    if (error.response) {
      console.log('MCP endpoint status:', error.response.status);
      console.log('MCP response data:', error.response.data);
    } else {
      console.error('Error testing server:', error.message);
    }
  }
}

testServer();