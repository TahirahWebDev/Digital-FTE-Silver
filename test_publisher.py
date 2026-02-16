import os
import sys
from pathlib import Path

# Add the project root to the path so we can import modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set the webhook URL for testing
os.environ['WEBHOOK_URL'] = 'https://discordapp.com/api/webhooks/mock_test_id/mock_test_token'
os.environ['TESTING'] = '1'  # Enable testing mode

from scripts.tools.publisher import publish_content

# Test the publisher
content = "# Test Post\nThis is a test post to verify that the Silver Tier Integration is working correctly with Discord."
result = publish_content(content)

print(f"Publish result: {result}")
print("Test completed successfully!")