import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the MCP server URL and OAuth settings
mcp_server_url = os.getenv('MCP_SERVER_INTERNAL_URL', 'http://localhost:8001')
client_id = os.getenv('OAUTH_CLIENT_ID', 'test_client')
client_secret = os.getenv('OAUTH_CLIENT_SECRET', 'test_secret')
redirect_uri = os.getenv('OAUTH_REDIRECT_URI', 'http://localhost:8000/oauth/callback')

# Define the registration request
registration_data = {
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uris": [redirect_uri],
    "scope": "memories:read memories:write",
    "token_endpoint_auth_method": "client_secret_post",
    "grant_types": ["authorization_code", "refresh_token"],
    "response_types": ["code"]
}

# Send the registration request
response = requests.post(
    f"{mcp_server_url}/oauth/register",
    json=registration_data
)

if response.status_code == 200:
    print("Client registration successful!")
    print("Response:", json.dumps(response.json(), indent=2))
else:
    print(f"Client registration failed with status {response.status_code}")
    print("Error:", response.text)
