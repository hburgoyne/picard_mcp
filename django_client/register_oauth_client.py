#!/usr/bin/env python
import os
import requests
import json
import sys
from dotenv import load_dotenv

def register_oauth_client():
    """Register OAuth client with the MCP server."""
    # Load environment variables
    load_dotenv()
    
    # Get MCP server URL
    # Use localhost with external port (8001) when running from host
    mcp_server_url = os.getenv('MCP_SERVER_URL', 'http://localhost:8001')
    
    # Prepare client registration data
    client_data = {
        'client_name': 'Picard MCP Django Client',
        'redirect_uris': [os.getenv('OAUTH_REDIRECT_URI', 'http://localhost:8000/oauth/callback')],
        'scopes': os.getenv('OAUTH_SCOPES', 'memories:read memories:write').split(),
        'is_confidential': True
    }
    
    print(f'Registering OAuth client with MCP server at {mcp_server_url}')
    print(f'Client data: {json.dumps(client_data, indent=2)}')
    
    try:
        # Send registration request to MCP server
        response = requests.post(
            f"{mcp_server_url}/api/oauth/register",
            json=client_data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Check response
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            
            print('OAuth client registered successfully!')
            print(f'Client ID: {result["client_id"]}')
            print(f'Client Secret: {result["client_secret"]}')
            
            # Update .env file with new client credentials
            update_env_file(result["client_id"], result["client_secret"])
            
            print('Updated .env file with new client credentials')
            return True
        else:
            print(f'Error registering OAuth client: {response.status_code}')
            print(response.text)
            return False
    
    except requests.exceptions.RequestException as e:
        print(f'Error connecting to MCP server: {str(e)}')
        return False

def update_env_file(client_id, client_secret):
    """Update the .env file with new client credentials."""
    env_file_path = '.env'
    
    # Read existing .env file
    with open(env_file_path, 'r') as f:
        lines = f.readlines()
    
    # Update client credentials
    updated_lines = []
    for line in lines:
        if line.startswith('OAUTH_CLIENT_ID='):
            updated_lines.append(f'OAUTH_CLIENT_ID={client_id}\n')
        elif line.startswith('OAUTH_CLIENT_SECRET='):
            updated_lines.append(f'OAUTH_CLIENT_SECRET={client_secret}\n')
        else:
            updated_lines.append(line)
    
    # Write updated .env file
    with open(env_file_path, 'w') as f:
        f.writelines(updated_lines)

if __name__ == '__main__':
    success = register_oauth_client()
    sys.exit(0 if success else 1)
