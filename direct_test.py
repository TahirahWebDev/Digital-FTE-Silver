import os
from dotenv import load_dotenv
load_dotenv()

# Set the webhook URL directly if not loaded from .env
if not os.getenv('WEBHOOK_URL'):
    os.environ['WEBHOOK_URL'] = 'https://discord.com/api/webhooks/1472832833667072083/d0Sw6uOqcxBjqUWL_2nupTxMVz9KK27umOrqSq426M6-CVSj0H2fR71YKvL-vxiztdU4'

from scripts.tools.publisher import publish_content

# Test the publisher directly
content = "# Test Post\nThis is a test post to verify that the Silver Tier Integration is working correctly with Discord."

print("Attempting to publish content...")
result = publish_content(content)
print(f"Publish result: {result}")