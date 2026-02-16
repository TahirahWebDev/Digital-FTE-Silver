# Set the environment variable
$env:WEBHOOK_URL = "https://discord.com/api/webhooks/1472832833667072083/d0Sw6uOqcxBjqUWL_2nupTxMVz9KK27umOrqSq426M6-CVSj0H2fR71YKvL-vxiztdU4"

# Change to the project directory
Set-Location -Path "F:\Tahirah\Hackathon-0\AI_Employee_Vault"

# Run the Silver Tier Integration
Write-Host "Starting Silver Tier Integration..."
Write-Host "Webhook URL is set: $($env:WEBHOOK_URL -ne $null)"
python run_silver_tier.py