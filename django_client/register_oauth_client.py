import os
import requests
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def register_oauth_client():
    """Register the OAuth client with the MCP server"""
    print("Registering OAuth client with MCP server...")
    
    # Get OAuth client details from environment variables
    client_id = os.getenv('OAUTH_CLIENT_ID', 'picard_client')
    client_secret = os.getenv('OAUTH_CLIENT_SECRET', 'picard_secret')
    redirect_uri = os.getenv('OAUTH_REDIRECT_URI', 'http://localhost:8000/oauth/callback')
    scopes = os.getenv('OAUTH_SCOPES', 'memories:read memories:write')
    
    # Use the internal URL for server-to-server communication
    mcp_server_url = os.getenv('MCP_SERVER_INTERNAL_URL', 'http://app:8000')
    
    # Build the registration URL
    registration_url = f"{mcp_server_url}/register"
    
    # Prepare the registration data
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uris': [redirect_uri],  # Ensure redirect_uris is a list
        'scopes': scopes.split()  # Split scopes into a list
    }
    
    print(f"Registration URL: {registration_url}")
    print(f"Client ID: {client_id}")
    print(f"Redirect URI: {redirect_uri}")
    print(f"Scopes: {scopes}")
    
    try:
        # Send the registration request
        response = requests.post(registration_url, json=data)
        
        if response.status_code == 200:
            print("OAuth client registration successful!")
            print(response.json())
            return True
        else:
            print(f"OAuth client registration failed: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"Error registering OAuth client: {e}")
        return False

if __name__ == "__main__":
    success = register_oauth_client()
    sys.exit(0 if success else 1)
