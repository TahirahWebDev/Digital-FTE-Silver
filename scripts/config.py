"""
Configuration settings for the Digital FTE Automation system.
"""

import os
from pathlib import Path

# Path to your Obsidian vault

# Hardcode your path here so you don't have to type it every time
VAULT_PATH = Path(r"F:\Tahirah\Hackathon-0\AI_Employee_Vault")
VAULT_PATH = os.getenv("VAULT_PATH", "")

# If VAULT_PATH is not set in environment, use a default path or raise an error
if not VAULT_PATH:
    # Use the current project directory as default for testing purposes
    VAULT_PATH = "F:\\Tahirah\\Hackathon-0\\AI_Employee_Vault"

VAULT_PATH = Path(VAULT_PATH)

# Folder names (can be customized if needed)
INBOX_FOLDER = "01_Inbox"
NEEDS_ACTION_FOLDER = "02_Needs_Action"
PENDING_APPROVAL_FOLDER = "03_Pending_Approval"
APPROVED_FOLDER_NAME = "04_Approved"  # Renamed to avoid conflict
DONE_FOLDER_NAME = "05_Done"  # Renamed to avoid conflict

# Full paths for each folder
INBOX_PATH = VAULT_PATH / INBOX_FOLDER
NEEDS_ACTION_PATH = VAULT_PATH / NEEDS_ACTION_FOLDER
PENDING_APPROVAL_PATH = VAULT_PATH / PENDING_APPROVAL_FOLDER
APPROVED_PATH = VAULT_PATH / APPROVED_FOLDER_NAME
DONE_PATH = VAULT_PATH / DONE_FOLDER_NAME

# Ensure all required folders exist
REQUIRED_FOLDERS = [
    INBOX_PATH,
    NEEDS_ACTION_PATH,
    PENDING_APPROVAL_PATH,
    APPROVED_PATH,
    DONE_PATH
]

# File extensions that the system will process
ALLOWED_EXTENSIONS = {'.txt', '.md'}

# Maximum file size allowed (in bytes) - 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# Characters to sanitize from filenames
INVALID_CHARS = '<>:"|?*'

# Log file path
LOG_FILE = "digital_fte.log"

# API Keys and External Services
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Configuration for the Silver Tier Integration
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')  # Discord webhook URL
API_CREDENTIALS = {
    'webhook_url': WEBHOOK_URL
}

# Silver Tier folder paths (relative to where the script runs)
SILVER_APPROVED_FOLDER = '04_Approved'
SILVER_DONE_FOLDER = '05_Done'

# Supported file extensions for Silver Tier
SUPPORTED_EXTENSIONS = ['.md', '.txt']