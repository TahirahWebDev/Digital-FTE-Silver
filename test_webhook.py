#!/usr/bin/env python3
"""Test script to debug webhook URL issue"""

import os
print(f"Environment WEBHOOK_URL: {repr(os.environ.get('WEBHOOK_URL'))}")

from scripts.config import API_CREDENTIALS, WEBHOOK_URL
print(f"Config WEBHOOK_URL: {repr(WEBHOOK_URL)}")
print(f"Config API_CREDENTIALS: {API_CREDENTIALS}")

from scripts.tools.publisher import post_to_discord_webhook
print("\nTesting post_to_discord_webhook...")
result = post_to_discord_webhook("Test message from debug script")
print(f"Result: {result}")
