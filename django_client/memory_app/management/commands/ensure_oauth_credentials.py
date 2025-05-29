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
        
        # Check if we're using default credentials or if forced
        using_defaults = (
            settings.OAUTH_CLIENT_ID == '550e8400-e29b-41d4-a716-446655440000' or 
            settings.OAUTH_CLIENT_SECRET == 'a_strong_random_secret_at_least_32_characters'
        )
        
        if not using_defaults and not force:
            self.stdout.write(
                self.style.SUCCESS('OAuth credentials are already configured')
            )
            return
        
        if using_defaults:
            self.stdout.write(
                self.style.WARNING('Using default OAuth credentials - attempting to register new client')
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
    
    def register_oauth_client(self):
        """Register OAuth client with the MCP server."""
        # Get MCP server URL - prefer internal URL for server-to-server communication
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
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Failed to save credentials to file: {e}')
                    )
                
                return True
            else:
                self.stdout.write(
                    self.style.ERROR(f'Registration failed: {response.status_code} - {response.text}')
                )
                return False
                
        except requests.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'Error connecting to MCP server: {e}')
            )
            return False
