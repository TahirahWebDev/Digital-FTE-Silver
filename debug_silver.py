import os
import sys
import time
from pathlib import Path

# Add the project root to the path so we can import modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set the webhook URL directly
os.environ['WEBHOOK_URL'] = 'https://discord.com/api/webhooks/1472832833667072083/d0Sw6uOqcxBjqUWL_2nupTxMVz9KK27umOrqSq426M6-CVSj0H2fR71YKvL-vxiztdU4'

print("Starting Silver Tier Integration with explicit configuration...")
print(f"Current working directory: {os.getcwd()}")

from scripts.tools.logic_bridge import start_logic_bridge

print("Starting Silver Tier Integration - Logic Bridge")
print("Watching 04_Approved folder for new content...")
print("Press Ctrl+C to stop")

try:
    start_logic_bridge()
except KeyboardInterrupt:
    print("\nSilver Tier Integration stopped.")
    sys.exit(0)
except Exception as e:
    print(f"Error running Silver Tier Integration: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)