"""
MCP Discord Client - Silver Tier MCP Integration

This module provides MCP-compliant Discord messaging.
It works in two modes:
1. MCP Mode: When MCP server is registered, AI assistants call it as a tool
2. Direct Mode: Falls back to direct webhook for Python script usage

The MCP server (discord-mcp-server/index.js) is the primary interface.
This Python client allows your existing Python code to benefit from MCP.
"""

import requests
import json
from pathlib import Path


# Load webhook URL from .env file in discord-mcp-server directory
def _load_webhook_url() -> str:
    """Load webhook URL from the MCP server's .env file."""
    script_dir = Path(__file__).parent  # scripts/tools
    project_root = script_dir.parent.parent
    env_path = project_root / "discord-mcp-server" / ".env"
    
    if not env_path.exists():
        print(f"Warning: .env not found at {env_path}")
        return None
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('DISCORD_WEBHOOK_URL='):
                url = line.split('=', 1)[1].strip().strip('"\'')
                return url
    
    print(f"Warning: DISCORD_WEBHOOK_URL not found in {env_path}")
    return None


def send_discord_message(message: str) -> bool:
    """
    Send a message to Discord.
    
    This is the main function for MCP-compliant Discord messaging.
    When your AI assistant has MCP registered, it will call the MCP tool directly.
    When running from Python scripts, this provides the same functionality.
    
    Args:
        message: The message content to send to Discord
        
    Returns:
        True if successful, False otherwise
    """
    webhook_url = _load_webhook_url()
    
    if not webhook_url:
        print("ERROR: Could not load Discord webhook URL")
        return False
    
    # Format the content for Discord (2000 char limit)
    payload = {
        "content": message[:2000]
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        if response.ok or response.status == 204:
            print(f"[MCP Discord] Message sent successfully")
            return True
        else:
            print(f"[MCP Discord] Error: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("[MCP Discord] Error: Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"[MCP Discord] Error: {e}")
        return False


def list_mcp_tools() -> list:
    """
    Returns the list of MCP tools this module supports.
    This is for documentation/introspection purposes.
    """
    return [
        {
            "name": "send_discord_message",
            "description": "Send a message to Discord via webhook. Use this to notify users about events, approvals, or status updates.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message content to send to Discord"
                    }
                },
                "required": ["message"]
            }
        }
    ]


# ============================================================================
# BACKWARD COMPATIBILITY: Drop-in replacement for publisher.py functions
# ============================================================================

def post_to_discord_webhook(content: str, webhook_url: str = None) -> bool:
    """
    Drop-in replacement for the old post_to_discord_webhook function.
    
    This maintains backward compatibility while using the MCP-compliant approach.
    The webhook_url parameter is ignored (we load from .env like MCP does).
    
    Args:
        content: The content to post
        webhook_url: Ignored (loads from discord-mcp-server/.env instead)
        
    Returns:
        True if successful, False otherwise
    """
    if webhook_url:
        print("Note: webhook_url parameter ignored when using MCP client (uses .env instead)")
    
    return send_discord_message(content)


def publish_content(content: str) -> bool:
    """
    Drop-in replacement for the old publish_content function.
    
    Args:
        content: The content to publish
        
    Returns:
        True if successful, False otherwise
    """
    return send_discord_message(content)


# ============================================================================
# TEST / DEMO
# ============================================================================

if __name__ == "__main__":
    print("Testing MCP Discord Client...")
    print("=" * 50)
    
    # Test 1: List available tools
    print("\n1. Available MCP tools:")
    tools = list_mcp_tools()
    for tool in tools:
        print(f"   - {tool['name']}: {tool['description'][:60]}...")
    
    # Test 2: Send a test message
    print("\n2. Sending test message:")
    test_message = "[MCP Test] If you see this, the MCP client is working!"
    success = send_discord_message(test_message)
    
    print("\n" + "=" * 50)
    if success:
        print("[SUCCESS] MCP Discord Client is working!")
    else:
        print("[FAILED] MCP Discord Client failed. Check webhook URL.")
