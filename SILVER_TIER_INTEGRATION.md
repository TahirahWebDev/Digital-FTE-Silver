# Silver Tier Integration

## Overview
The Silver Tier Integration enables automatic posting of approved content to Discord when files are moved to the `04_Approved` folder.

## Components

### 1. Publisher (`scripts/tools/publisher.py`)
Handles posting content to external platforms:
- `post_to_discord_webhook()`: Posts content to a Discord webhook
- `publish_content()`: Main function to publish content to Discord

### 2. Logic Bridge (`scripts/tools/logic_bridge.py`)
Monitors the `04_Approved` folder and processes new files:
- Watches for file creation/movement to the approved folder
- Reads content from approved files
- Calls the publisher to post content to Discord
- Moves successfully posted files to `05_Done` folder with a timestamp

### 3. Configuration (`scripts/config.py`)
Contains configuration settings:
- Discord webhook URL
- Folder paths
- Supported file extensions

## Setup

### Environment Variables
Set this environment variable:
```bash
export WEBHOOK_URL="your_discord_webhook_url"
```

### Dependencies
Install required packages:
```bash
poetry install
```

## Usage

1. Ensure the Silver Tier Integration is running:
   ```bash
   python run_silver_tier.py
   ```

2. Move a content file (`.md` or `.txt`) to the `04_Approved` folder

3. The system will:
   - Automatically detect the new file
   - Read its content
   - Post it to Discord
   - Move the file to `05_Done` with a timestamp if successful

## Testing

Run the tests:
```bash
python -m pytest test_silver_tier.py -v
```

## Supported Platforms

Currently supports:
- Discord (via webhooks)

## File Flow

```
Draft in 01_Inbox → Move to 02_Needs_Action → Move to 03_Pending_Approval → Move to 04_Approved → Auto-post to Discord → Move to 05_Done
```

## Troubleshooting

- If content isn't posting, check that the WEBHOOK_URL environment variable is set correctly
- Verify the Discord webhook URL is valid
- Check logs for error messages
- Ensure the `04_Approved` and `05_Done` folders exist