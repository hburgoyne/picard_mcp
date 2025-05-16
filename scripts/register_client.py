import os
import sys

# First, let's fix the attribute name mismatch in the provider.py file
provider_path = '/app/app/auth/provider.py'

with open(provider_path, 'r') as f:
    content = f.read()

# Replace 'allowed_scopes=client_info.scopes' with 'allowed_scopes=client_info.scope.split()'
# Also fix the redirect_uris handling
fixed_content = content.replace(
    'allowed_scopes=client_info.scopes', 
    'allowed_scopes=client_info.scope.split()'
).replace(
    'redirect_uris=[uri for uri in client.redirect_uris]',
    'redirect_uris=[str(uri) for uri in client.redirect_uris]'
)

with open(provider_path, 'w') as f:
    f.write(fixed_content)

print("Fixed the attribute name mismatch in provider.py")

# Now let's register the client
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the MCP server URL and OAuth settings
mcp_server_url = os.getenv('MCP_SERVER_INTERNAL_URL', 'http://app:8000')
client_id = os.getenv('OAUTH_CLIENT_ID', 'picard_client')
client_secret = os.getenv('OAUTH_CLIENT_SECRET', 'picard_secret')
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
