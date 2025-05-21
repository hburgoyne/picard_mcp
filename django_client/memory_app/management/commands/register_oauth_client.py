from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import json
import os
from dotenv import load_dotenv

class Command(BaseCommand):
    help = 'Register OAuth client with the MCP server'

    def handle(self, *args, **options):
        # Load environment variables
        load_dotenv()
        
        # Get MCP server URL
        mcp_server_url = os.getenv('MCP_SERVER_INTERNAL_URL', settings.MCP_SERVER_INTERNAL_URL)
        
        # Prepare client registration data
        client_data = {
            'client_name': 'Picard MCP Django Client',
            'redirect_uris': [os.getenv('OAUTH_REDIRECT_URI', settings.OAUTH_REDIRECT_URI)],
            'scopes': os.getenv('OAUTH_SCOPES', settings.OAUTH_SCOPES).split(),
            'is_confidential': True
        }
        
        self.stdout.write(self.style.SUCCESS(f'Registering OAuth client with MCP server at {mcp_server_url}'))
        self.stdout.write(f'Client data: {json.dumps(client_data, indent=2)}')
        
        try:
            # Send registration request to MCP server
            response = requests.post(
                f"{mcp_server_url}/register",
                json=client_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Check response
            if response.status_code == 200 or response.status_code == 201:
                result = response.json()
                
                self.stdout.write(self.style.SUCCESS('OAuth client registered successfully!'))
                self.stdout.write(f'Client ID: {result["client_id"]}')
                self.stdout.write(f'Client Secret: {result["client_secret"]}')
                
                # Update .env file with new client credentials
                self.update_env_file(result["client_id"], result["client_secret"])
                
                self.stdout.write(self.style.SUCCESS('Updated .env file with new client credentials'))
            else:
                self.stdout.write(self.style.ERROR(f'Error registering OAuth client: {response.status_code}'))
                self.stdout.write(response.text)
        
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Error connecting to MCP server: {str(e)}'))
    
    def update_env_file(self, client_id, client_secret):
        """Update the .env file with new client credentials."""
        env_file_path = os.path.join(settings.BASE_DIR, '.env')
        
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
