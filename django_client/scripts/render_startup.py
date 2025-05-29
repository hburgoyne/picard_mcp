#!/usr/bin/env python
"""
Render startup script for Django client.
Handles database migrations and OAuth client registration.
"""
import os
import sys
import subprocess
import requests
import json
import base64
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def wait_for_database():
    """Wait for database to be available."""
    import psycopg2
    from psycopg2 import OperationalError
    
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT', '5432'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME')
            )
            conn.close()
            print("Database connection successful")
            return True
        except OperationalError:
            retry_count += 1
            print(f"Database not ready, retrying... ({retry_count}/{max_retries})")
            time.sleep(2)
    
    print("Database connection failed after maximum retries")
    return False

def wait_for_mcp_server():
    """Wait for MCP server to be available."""
    mcp_server_url = os.getenv('MCP_SERVER_URL', 'https://picard-mcp-server.onrender.com')
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = requests.get(f"{mcp_server_url}/health", timeout=10)
            if response.status_code == 200:
                print("MCP server is available")
                return True
        except requests.RequestException:
            pass
        
        retry_count += 1
        print(f"MCP server not ready, retrying... ({retry_count}/{max_retries})")
        time.sleep(10)
    
    print("MCP server connection failed after maximum retries")
    return False

def run_migrations():
    """Run Django database migrations."""
    print("Running Django migrations...")
    
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'migrate'
        ], check=True, capture_output=True, text=True, cwd=project_root)
        print("Migrations completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Migration failed: {e.stderr}")
        return False

def collect_static_files():
    """Collect Django static files."""
    print("Collecting static files...")
    
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'collectstatic', '--noinput'
        ], check=True, capture_output=True, text=True, cwd=project_root)
        print("Static files collected successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Static file collection failed: {e.stderr}")
        return False

def register_oauth_client():
    """Register OAuth client with the MCP server."""
    print("Registering OAuth client...")
    
    mcp_server_url = os.getenv('MCP_SERVER_URL', 'https://picard-mcp-server.onrender.com')
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD')
    redirect_uri = os.getenv('OAUTH_REDIRECT_URI', 'https://picard-django-client.onrender.com/oauth/callback')
    
    print(f"MCP Server URL: {mcp_server_url}")
    print(f"Admin Username: {admin_username}")
    print(f"Admin Password: {'SET' if admin_password else 'NOT SET'}")
    print(f"Redirect URI: {redirect_uri}")
    
    if not admin_password:
        print("ADMIN_PASSWORD not set, skipping OAuth client registration")
        return False
    
    # Create basic auth header
    auth_credentials = f"{admin_username}:{admin_password}"
    auth_header = base64.b64encode(auth_credentials.encode()).decode()
    
    # Prepare client registration data
    client_data = {
        'client_name': 'Picard MCP Django Client (Render)',
        'redirect_uris': [redirect_uri],
        'scopes': ['memories:read', 'memories:write'],
        'is_confidential': True
    }
    
    headers = {
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/json'
    }
    
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
            
            print(f"OAuth client registered successfully")
            print(f"Client ID: {client_id}")
            print(f"Client Secret: {client_secret[:8]}...")  # Show partial secret for debugging
            
            # Set environment variables for the running process
            os.environ['OAUTH_CLIENT_ID'] = client_id
            os.environ['OAUTH_CLIENT_SECRET'] = client_secret
            
            # Also write to a file that can be sourced later if needed
            with open('/tmp/oauth_credentials.env', 'w') as f:
                f.write(f"OAUTH_CLIENT_ID={client_id}\n")
                f.write(f"OAUTH_CLIENT_SECRET={client_secret}\n")
            
            # IMPORTANT: For Render deployment, also set the environment variables
            # in a way that they persist to the Django process
            # Write to a Python file that can be imported
            with open('/tmp/oauth_credentials.py', 'w') as f:
                f.write(f"OAUTH_CLIENT_ID = '{client_id}'\n")
                f.write(f"OAUTH_CLIENT_SECRET = '{client_secret}'\n")
            
            print("OAuth credentials saved to environment and /tmp/oauth_credentials.env")
            return True
        else:
            print(f"OAuth client registration failed: {response.status_code} - {response.text}")
            # Try to parse the error response for more details
            try:
                error_details = response.json()
                print(f"Error details: {error_details}")
            except:
                print("Could not parse error response as JSON")
            return False
            
    except requests.RequestException as e:
        print(f"OAuth client registration error: {e}")
        return False

def main():
    """Main startup function."""
    print("Starting Django client startup tasks...")
    
    # Wait for database
    if not wait_for_database():
        sys.exit(1)
    
    # Run migrations
    if not run_migrations():
        sys.exit(1)
    
    # Collect static files
    if not collect_static_files():
        print("Warning: Static file collection failed, continuing...")
    
    # Wait for MCP server and register OAuth client
    if wait_for_mcp_server():
        if not register_oauth_client():
            print("Warning: OAuth client registration failed, continuing...")
    else:
        print("Warning: MCP server not available, skipping OAuth registration")
    
    print("Django client startup tasks completed")

if __name__ == "__main__":
    main()
