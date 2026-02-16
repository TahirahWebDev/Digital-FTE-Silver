"""
Demo script to showcase the Silver Tier Integration functionality
"""
import os
import time
from pathlib import Path
import tempfile

def demo_setup():
    print("Setting up Silver Tier Integration Demo")
    print("="*50)
    
    # Show the folder structure
    print("Folder structure:")
    print("|-- 04_Approved/ (watches for new content)")
    print("|-- 05_Done/ (moves posted content here)")
    print("|-- scripts/")
    print("|   |-- config.py (stores API credentials)")
    print("|   `-- tools/")
    print("|       |-- publisher.py (posts to external platforms)")
    print("|       `-- logic_bridge.py (watches for new files)")
    print("|-- run_silver_tier.py (starts the integration)")
    print()
    
    # Check if required folders exist
    approved_folder = Path("../04_Approved")
    done_folder = Path("../05_Done")
    
    print(f"OK Approved folder exists: {approved_folder.exists()}")
    print(f"OK Done folder exists: {done_folder.exists()}")
    
    print()
    print("Configuration:")
    print("- Uses WEBHOOK_URL environment variable for Discord")
    print("- Supports .md and .txt file extensions")
    print()
    
    print("To use the Silver Tier Integration:")
    print("1. Set your environment variable:")
    print("   export WEBHOOK_URL='your_discord_webhook_url'")
    print("2. Start the service: python run_silver_tier.py")
    print("3. Move a .md or .txt file to 04_Approved folder")
    print("4. Watch as it gets posted to Discord and moved to 05_Done")
    print()
    
    print("Demo completed successfully!")
    print("The Silver Tier Integration is ready to use.")

if __name__ == "__main__":
    demo_setup()