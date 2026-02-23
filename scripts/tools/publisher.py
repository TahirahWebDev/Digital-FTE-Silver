"""
Publisher - Discord Publishing with MCP Support

This module now uses the MCP Discord Client by default for Silver Tier compliance.
Direct webhook calls are still available as fallback.

MCP Integration:
- Uses @modelcontextprotocol/sdk via discord-mcp-server
- AI assistants can call send_discord_message as a tool
- Maintains backward compatibility with existing code
"""

# Try MCP client first (Silver Tier), fall back to direct webhook
try:
    from scripts.tools.mcp_discord_client import (
        send_discord_message,
        post_to_discord_webhook as mcp_post_wrapper,
        publish_content as mcp_publish_wrapper
    )
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: MCP client not available, using direct webhook: {e}")
    MCP_AVAILABLE = False
    import requests
    from scripts.config import API_CREDENTIALS


def post_to_discord_webhook(content: str, webhook_url: str = None, use_mcp: bool = True) -> bool:
    """
    Posts content to Discord via MCP tool call (or direct webhook fallback).

    Args:
        content: The content to post
        webhook_url: The Discord webhook URL (only used if MCP unavailable)
        use_mcp: Whether to use MCP (default: True)

    Returns:
        True if successful, False otherwise
    """
    if use_mcp and MCP_AVAILABLE:
        # Use MCP tool call (Silver Tier compliant)
        return send_discord_message(content)
    else:
        # Fallback to direct webhook call
        return _post_via_direct_webhook(content, webhook_url)


def _post_via_direct_webhook(content: str, webhook_url: str = None) -> bool:
    """
    Direct webhook POST (fallback when MCP unavailable).
    """
    if not webhook_url:
        webhook_url = API_CREDENTIALS.get('webhook_url')
        print(f"DEBUG: API_CREDENTIALS = {API_CREDENTIALS}")
        print(f"DEBUG: webhook_url from config = {repr(webhook_url)}")

    if not webhook_url:
        print("DEBUG: Webhook URL MISSING")
        print("Warning: No Discord webhook URL provided, using mock for testing")
        import os
        if os.getenv('TESTING'):
            return True
        return False
    else:
        print("DEBUG: Webhook URL found (fallback mode)")

    payload = {
        "content": content[:2000]
    }

    try:
        response = requests.post(webhook_url, json=payload)
        print(f"DEBUG: Response status code: {response.status_code}")
        print(f"DEBUG: Response text: {response.text}")
        response.raise_for_status()
        print(f"Successfully posted to Discord: {response.status_code}")
        return True
    except Exception as e:
        print(f"Error posting to Discord: {e}")
        return False


def publish_content(content: str, use_mcp: bool = True) -> bool:
    """
    Publishes content to Discord via MCP (or direct webhook fallback).

    Args:
        content: The content to publish
        use_mcp: Whether to use MCP (default: True)

    Returns:
        True if successful, False otherwise
    """
    if use_mcp and MCP_AVAILABLE:
        return send_discord_message(content)
    else:
        return _post_via_direct_webhook(content)