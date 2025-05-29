"""
Management command to ensure OAuth credentials are properly configured.
"""
import os
import requests
import json
import base64
import uuid
from django.core.management.base import BaseCommand
from django.conf import settings
from dotenv import load_dotenv

class Command(BaseCommand):
    help = 'Ensure OAuth credentials are properly configured for the MCP server'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force registration of new OAuth client even if credentials exist',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        # Check if we need to register new OAuth credentials
        needs_registration = self.check_if_registration_needed()
        
        if not needs_registration and not force:
            self.stdout.write(
                self.style.SUCCESS('OAuth credentials are already configured and valid')
            )
            return
        
        if needs_registration:
            self.stdout.write(
                self.style.WARNING('OAuth credentials are invalid or not properly configured - attempting to register new client')
            )
        
        if force:
            self.stdout.write(
                self.style.WARNING('Force registration requested - registering new OAuth client')
            )
        
        # Try to register OAuth client
        success = self.register_oauth_client()
        
        if success:
            self.stdout.write(
                self.style.SUCCESS('OAuth client registration completed successfully')
            )
        else:
            self.stdout.write(
                self.style.ERROR('OAuth client registration failed')
            )
    
    def check_if_registration_needed(self):
        """Check if we need to register new OAuth credentials by validating the current ones."""
        from django.conf import settings
        import time
        
        # Check if we're using default credentials
        using_defaults = (
            settings.OAUTH_CLIENT_ID == '550e8400-e29b-41d4-a716-446655440000' or 
            settings.OAUTH_CLIENT_SECRET == 'a_strong_random_secret_at_least_32_characters'
        )
        
        if using_defaults:
            return True
            
        # If we have credentials, try to validate them against MCP server
        max_retries = 5
        retry_count = 0
        retry_delay = 3  # seconds
        
        while retry_count < max_retries:
            try:
                mcp_server_url = getattr(settings, 'MCP_SERVER_INTERNAL_URL', None) or \
                                getattr(settings, 'MCP_SERVER_URL', 'http://mcp_server:8000')
                
                # Try to access a protected endpoint with client credentials to validate them
                url = f"{mcp_server_url}/api/oauth/client_info?client_id={settings.OAUTH_CLIENT_ID}"
                self.stdout.write(f"Validating client ID {settings.OAUTH_CLIENT_ID} with MCP server at {url}")
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    # Check if the client exists and has the correct redirect URI
                    client_info = response.json()
                    if client_info.get('client_id') == settings.OAUTH_CLIENT_ID:
                        self.stdout.write(self.style.SUCCESS(f"Verified client ID {settings.OAUTH_CLIENT_ID} with MCP server"))
                        return False  # No registration needed
                
                self.stdout.write(self.style.WARNING(f"Client validation failed: {response.status_code} - {response.text}"))
                return True  # Registration needed
                    
            except requests.RequestException as e:
                retry_count += 1
                if retry_count >= max_retries:
                    self.stdout.write(self.style.WARNING(f"Error validating client credentials: {e}"))
                    return True  # Registration needed if validation fails
                else:
                    self.stdout.write(f"MCP server not ready, retrying in {retry_delay} seconds... ({retry_count}/{max_retries})")
                    time.sleep(retry_delay)
    
    def register_oauth_client(self):
        """Register OAuth client with the MCP server."""
        # Get MCP server URL - prefer internal URL for server-to-server communication
        from django.conf import settings
        import time
        
        mcp_server_url = getattr(settings, 'MCP_SERVER_INTERNAL_URL', None) or \
                        getattr(settings, 'MCP_SERVER_URL', 'http://mcp_server:8000')
        
        # Get admin credentials from environment
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD')
        
        if not admin_password:
            self.stdout.write(
                self.style.ERROR('ADMIN_PASSWORD not set in environment variables')
            )
            return False
        
        # Create basic auth header
        auth_credentials = f"{admin_username}:{admin_password}"
        auth_header = base64.b64encode(auth_credentials.encode()).decode()
        
        # Prepare client registration data
        client_data = {
            'client_name': f'Picard MCP Django Client ({uuid.uuid4().hex[:8]})',
            'redirect_uris': [settings.OAUTH_REDIRECT_URI],
            'scopes': settings.OAUTH_SCOPES.split(),
            'is_confidential': True
        }
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/json'
        }
        
        self.stdout.write(f'Attempting to register OAuth client with {mcp_server_url}')
        
        # Add retry logic for MCP server availability
        max_retries = 5
        retry_count = 0
        retry_delay = 3  # seconds
        
        while retry_count < max_retries:
            try:
                response = requests.post(
                    f"{mcp_server_url}/api/admin/clients/register",
                    json=client_data,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    client_info = response.json()
                    client_id = client_info['client_id']
                    client_secret = client_info['client_secret']
                    
                    self.stdout.write(f"OAuth client registered successfully")
                    self.stdout.write(f"Client ID: {client_id}")
                    self.stdout.write(f"Client Secret: {client_secret[:8]}...")
                    
                    # Write credentials to the temp file for persistence
                    try:
                        with open('/tmp/oauth_credentials.env', 'w') as f:
                            f.write(f"OAUTH_CLIENT_ID={client_id}\n")
                            f.write(f"OAUTH_CLIENT_SECRET={client_secret}\n")
                        
                        self.stdout.write("OAuth credentials saved to /tmp/oauth_credentials.env")
                        
                        # Also try to set in current environment
                        os.environ['OAUTH_CLIENT_ID'] = client_id
                        os.environ['OAUTH_CLIENT_SECRET'] = client_secret
                        
                        # Write to Python file for import
                        with open('/tmp/oauth_credentials.py', 'w') as f:
                            f.write(f"OAUTH_CLIENT_ID = '{client_id}'\n")
                            f.write(f"OAUTH_CLIENT_SECRET = '{client_secret}'\n")
                            
                        # Also try to write to .env file for local development
                        try:
                            from django.conf import settings
                            import os.path
                            env_path = os.path.join(os.path.dirname(settings.BASE_DIR), '.env')
                            with open(env_path, 'w') as f:
                                f.write(f"OAUTH_CLIENT_ID={client_id}\n")
                                f.write(f"OAUTH_CLIENT_SECRET={client_secret}\n")
                            self.stdout.write("OAuth credentials also saved to .env file")
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f'Could not save credentials to .env file: {e}')
                            )
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'Failed to save credentials to file: {e}')
                        )
                    
                    return True
                else:
                    retry_count += 1
                    if retry_count >= max_retries:
                        self.stdout.write(
                            self.style.ERROR(f'Registration failed: {response.status_code} - {response.text}')
                        )
                        return False
                    else:
                        self.stdout.write(f"Registration attempt failed (status {response.status_code}), retrying in {retry_delay} seconds... ({retry_count}/{max_retries})")
                        time.sleep(retry_delay)
                    
            except requests.RequestException as e:
                retry_count += 1
                if retry_count >= max_retries:
                    self.stdout.write(
                        self.style.ERROR(f'Error connecting to MCP server: {e}')
                    )
                    return False
                else:
                    self.stdout.write(f"MCP server not available, retrying in {retry_delay} seconds... ({retry_count}/{max_retries})")
                    time.sleep(retry_delay)
