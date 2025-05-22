#!/usr/bin/env python
import os
import requests
import json
import sys
import argparse
import base64
from dotenv import load_dotenv

def register_oauth_client(update=False, client_id=None):
    """Register OAuth client with the MCP server."""
    # Load environment variables
    load_dotenv()
    
    # Get MCP server URL
    # When running inside Docker, use the internal Docker network hostname
    # MCP_SERVER_INTERNAL_URL is for container-to-container communication
    # MCP_SERVER_URL is for external access (from browser)
    mcp_server_url = os.getenv('MCP_SERVER_INTERNAL_URL', 'http://mcp_server:8000')
    
    # Get admin credentials
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD', 'adminpassword')
    
    # Create basic auth header
    auth_credentials = f"{admin_username}:{admin_password}"
    auth_header = base64.b64encode(auth_credentials.encode()).decode()
    
    # Prepare client registration data
    client_data = {
        'client_name': 'Picard MCP Django Client',
        'redirect_uris': [os.getenv('OAUTH_REDIRECT_URI', 'http://localhost:8000/oauth/callback')],
        'scopes': os.getenv('OAUTH_SCOPES', 'memories:read memories:write').split(),
        'is_confidential': True
    }
    
    if update and client_id:
        print(f'Updating OAuth client with ID: {client_id} at {mcp_server_url}')
    else:
        print(f'Registering new OAuth client with MCP server at {mcp_server_url}')
        
    print(f'Client data: {json.dumps(client_data, indent=2)}')
    
    # Prepare headers with authentication
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {auth_header}'
    }
    
    try:
        if update and client_id:
            # Send update request to MCP server
            response = requests.put(
                f"{mcp_server_url}/api/admin/clients/{client_id}",
                json=client_data,
                headers=headers
            )
        else:
            # Send registration request to MCP server
            response = requests.post(
                f"{mcp_server_url}/api/admin/clients/register",
                json=client_data,
                headers=headers
            )
        
        # Check response
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            
            if update and client_id:
                print('OAuth client updated successfully!')
                print(f'Client ID: {result["client_id"]}')
                # When updating, we don't get a new client secret
                if "client_secret" in result:
                    print(f'Client Secret: {result["client_secret"]}')
                    # Update .env file with new client credentials
                    update_env_file(result["client_id"], result["client_secret"])
                    print('Updated .env file with new client credentials')
                else:
                    print('Client secret unchanged')
            else:
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
    parser = argparse.ArgumentParser(description='Register or update OAuth client with MCP server')
    parser.add_argument('--update', action='store_true', help='Update existing client instead of registering new one')
    parser.add_argument('--client-id', type=str, help='Client ID to update (required with --update)')
    args = parser.parse_args()
    
    if args.update and not args.client_id:
        print('Error: --client-id is required when using --update')
        sys.exit(1)
    
    success = register_oauth_client(update=args.update, client_id=args.client_id)
    sys.exit(0 if success else 1)
