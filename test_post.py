#!/usr/bin/env python3
"""
Standalone script to test Discord webhook connection
"""

import os
import requests

def test_discord_connection():
    webhook_url = os.getenv('WEBHOOK_URL')
    
    if not webhook_url:
        print("ERROR: WEBHOOK_URL environment variable not set!")
        print("Please set your Discord webhook URL:")
        print("export WEBHOOK_URL='your_discord_webhook_url_here'")
        return False
    
    print(f"Using webhook URL: {webhook_url[:30]}...")  # Show partial URL for security
    
    # Prepare the payload
    payload = {
        "content": "Hello! This is a test message from the AI Employee Vault."
    }
    
    try:
        print("Sending test message to Discord...")
        response = requests.post(webhook_url, json=payload)
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 204:
            print("✅ SUCCESS: Message sent to Discord!")
            return True
        else:
            print(f"❌ FAILED: Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to Discord: {e}")
        return False

if __name__ == "__main__":
    print("Testing Discord Webhook Connection...")
    print("="*50)
    success = test_discord_connection()
    
    if success:
        print("\nSUCCESS: Discord connection test completed successfully!")
    else:
        print("\nFAILED: Discord connection test failed!")
        print("Please check your webhook URL and internet connection.")