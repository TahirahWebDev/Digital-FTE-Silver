"""
Xero OAuth2 Handshake - Get Your Access Token

Run this script to complete the Xero OAuth2 handshake and get your access token.

Steps:
1. Run: python scripts/tools/xero_oauth.py
2. Open the URL in your browser
3. Connect your Xero organization
4. Copy the redirect URL
5. Paste it back in the terminal
6. Get your access token and tenant ID!
"""

import webbrowser
import urllib.parse
import urllib.request
import json
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import os
from pathlib import Path

# Your Xero App Credentials (from .env or here)
CLIENT_ID = "5B28A3D21DE741D19781FFCF0E0FF25A"  # From your .env
CLIENT_SECRET = "xqGCqYB9N7XFgFOT0UfblWdffH9XHmuxG4UO_FAycnIyHMfm"  # From your .env
REDIRECT_URI = "http://localhost:8080"

# Xero OAuth URLs
AUTHORIZATION_URL = "https://login.xero.com/identity/connect/authorize"
TOKEN_URL = "https://identity.xero.com/connect/token"
CONNECTIONS_URL = "https://api.xero.com/connections"

# Required scopes
SCOPES = [
    "openid",
    "profile", 
    "email",
    "offline_access",  # For refresh token
    "accounting.transactions"  # For manual journals
]


class XeroCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from Xero"""
    
    def do_GET(self):
        """Handle GET request (OAuth callback)"""
        global auth_code
        
        # Extract authorization code from URL
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if 'code' in params:
            auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            response = """
            <html>
            <head><title>Xero Authorization Successful</title></head>
            <body>
                <h1>✅ Xero Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                <script>window.close();</script>
            </body>
            </html>
            """
            self.wfile.write(response.encode())
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Authorization failed')


def get_authorization_url():
    """Generate Xero authorization URL"""
    scope_string = ' '.join(SCOPES)
    
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': scope_string,
        'state': 'gold_tier_xero_auth'
    }
    
    return f"{AUTHORIZATION_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(code):
    """Exchange authorization code for access token"""
    
    # Create authorization header
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    # Prepare request
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Make request
    req = urllib.request.Request(
        TOKEN_URL,
        data=urllib.parse.urlencode(data).encode(),
        headers=headers,
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            return result
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(f"Response: {e.read().decode()}")
        return None
    except Exception as e:
        print(f"Error exchanging code: {e}")
        return None


def get_tenant_id(access_token):
    """Get tenant ID from Xero connections"""
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    req = urllib.request.Request(
        CONNECTIONS_URL,
        headers=headers
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            connections = json.loads(response.read().decode())
            if connections:
                return connections[0].get('tenantId')
            return None
    except Exception as e:
        print(f"Error getting connections: {e}")
        return None


def save_to_env(access_token, tenant_id):
    """Save credentials to .env file"""
    env_path = Path(__file__).parent.parent.parent / ".env"
    
    if not env_path.exists():
        print(f"⚠️  .env file not found at {env_path}")
        return False
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update access token (add if not exists)
        if "XERO_ACCESS_TOKEN=" in content:
            import re
            content = re.sub(
                r'XERO_ACCESS_TOKEN=.*',
                f'XERO_ACCESS_TOKEN={access_token}',
                content
            )
        else:
            content += f"\nXERO_ACCESS_TOKEN={access_token}\n"
        
        # Update tenant ID
        if "XERO_TENANT_ID=" in content:
            import re
            content = re.sub(
                r'XERO_TENANT_ID=.*',
                f'XERO_TENANT_ID={tenant_id}',
                content
            )
        else:
            content += f"\nXERO_TENANT_ID={tenant_id}\n"
        
        # Write back
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Credentials saved to {env_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving to .env: {e}")
        return False


def main():
    """Main OAuth flow"""
    global auth_code
    auth_code = None
    
    print("\n" + "="*60)
    print("Xero OAuth2 Handshake")
    print("="*60)
    print("\n📋 Required Scopes:")
    for scope in SCOPES:
        print(f"   - {scope}")
    print("\nStep 1: Opening Xero authorization page...")
    
    # Start callback server
    server = HTTPServer(('localhost', 8080), XeroCallbackHandler)
    server_thread = threading.Thread(target=server.handle_request)
    server_thread.daemon = True
    server_thread.start()
    
    # Open browser
    auth_url = get_authorization_url()
    print(f"🔗 Opening: {auth_url[:80]}...")
    webbrowser.open(auth_url)
    
    print("\nStep 2: Waiting for authorization...")
    print("   (Connect your Xero organization in your browser)")
    
    # Wait for callback (max 5 minutes)
    import time
    start_time = time.time()
    while auth_code is None and (time.time() - start_time) < 300:
        time.sleep(0.5)
    
    if auth_code:
        print("\n✅ Authorization code received!")
        print("\nStep 3: Exchanging code for access token...")
        
        token_result = exchange_code_for_token(auth_code)
        
        if token_result:
            access_token = token_result.get('access_token')
            refresh_token = token_result.get('refresh_token')
            expires_in = token_result.get('expires_in', 1800)
            
            print("\n" + "="*60)
            print("✅ SUCCESS! Access Token Received")
            print("="*60)
            print(f"\nAccess Token: {access_token[:50]}...")
            print(f"Refresh Token: {refresh_token[:50]}...")
            print(f"⏰ Expires in: {expires_in} seconds ({expires_in/60:.1f} minutes)")
            
            # Get tenant ID
            print("\nStep 4: Getting tenant ID...")
            tenant_id = get_tenant_id(access_token)
            
            if tenant_id:
                print(f"✅ Tenant ID: {tenant_id}")
                
                # Save to .env
                print("\nStep 5: Saving to .env file...")
                save_to_env(access_token, tenant_id)
                
                print("\n" + "="*60)
                print("🎉 Xero Setup Complete!")
                print("="*60)
                print("\nYour Gold Tier agent can now log to Xero!")
                print("Restart the Logic Bridge to use Xero integration.")
                print("="*60 + "\n")
                
            else:
                print("❌ Failed to get tenant ID")
        else:
            print("\n❌ Failed to get access token")
    else:
        print("\n❌ Authorization timeout")
    
    server.server_close()


if __name__ == "__main__":
    print("\n⚠️  Xero OAuth2 Handshake")
    print("\nThis will:")
    print("1. Open your browser to authorize Xero")
    print("2. Get an access token")
    print("3. Get your tenant ID")
    print("4. Save both to your .env file")
    print("\nMake sure your Xero app is configured at:")
    print("https://developer.xero.com/app/manage")
    print("\nPress Enter to continue or Ctrl+C to exit...")
    input()
    
    main()
