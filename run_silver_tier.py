#!/usr/bin/env python3
"""
Silver Tier Integration Runner
Starts the logic bridge that watches the 04_Approved folder and posts content to external platforms
"""

import sys
import os
from pathlib import Path

# Add the project root to the path so we can import modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scripts.tools.logic_bridge import start_logic_bridge

if __name__ == "__main__":
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
        sys.exit(1)