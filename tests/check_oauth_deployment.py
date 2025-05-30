#!/usr/bin/env python
"""
Deployment OAuth Check Tool

This script verifies OAuth credential setup between Django client and MCP server
in a deployed environment like Render.com.

Usage:
    python check_oauth_deployment.py --mcp-url URL --django-url URL [--admin-password PASSWORD]

Example:
    python check_oauth_deployment.py \
        --mcp-url https://picard-mcp-server.onrender.com \
        --django-url https://picard-django-client.onrender.com
"""
import argparse
import logging
import os
import sys
import requests
import json
import base64
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('oauth_check')

def check_mcp_server(mcp_url):
    """Check MCP server health and basic connectivity."""
    logger.info(f"Checking MCP server at {mcp_url}")
    
    try:
        # Check health endpoint
        response = requests.get(f"{mcp_url}/health", timeout=10)
        if response.status_code == 200:
            logger.info("MCP server health check: OK")
        else:
            logger.error(f"MCP server health check failed: {response.status_code}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error connecting to MCP server: {e}")
        return False

def check_django_client(django_url):
    """Check Django client health and basic connectivity."""
    logger.info(f"Checking Django client at {django_url}")
    
    try:
        # Check health endpoint
        response = requests.get(f"{django_url}/health/", timeout=10)
        if response.status_code == 200:
            logger.info("Django client health check: OK")
            data = response.json()
            
            # Check if OAuth info is included in the health response
            if 'oauth' in data:
                oauth_info = data['oauth']
                logger.info(f"OAuth client ID: {oauth_info.get('client_id', 'Not configured')}")
                logger.info(f"Using default credentials: {oauth_info.get('using_default_credentials', True)}")
                logger.info(f"MCP validation: {oauth_info.get('mcp_validated', False)}")
                
                return oauth_info
            else:
                logger.warning("No OAuth information in health response")
                return None
        else:
            logger.error(f"Django client health check failed: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error connecting to Django client: {e}")
        return None

def check_client_registration(mcp_url, client_id):
    """Check if a client ID is registered with the MCP server."""
    logger.info(f"Checking client ID {client_id} registration with MCP server")
    
    try:
        response = requests.get(
            f"{mcp_url}/api/oauth/client_info?client_id={client_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            client_info = response.json()
            logger.info(f"Client info: {json.dumps(client_info, indent=2)}")
            return True
        else:
            logger.error(f"Client validation failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error checking client registration: {e}")
        return False

def register_new_client(mcp_url, admin_username, admin_password, redirect_uri):
    """Register a new OAuth client with the MCP server."""
    logger.info(f"Registering new OAuth client with MCP server")
    
    # Create basic auth header
    auth_credentials = f"{admin_username}:{admin_password}"
    auth_header = base64.b64encode(auth_credentials.encode()).decode()
    
    # Prepare client registration data
    client_data = {
        'client_name': f'Debug Client ({uuid.uuid4().hex[:8]})',
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
            f"{mcp_url}/api/admin/clients/register",
            json=client_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            client_info = response.json()
            logger.info(f"OAuth client registered successfully")
            logger.info(f"Client ID: {client_info['client_id']}")
            logger.info(f"Client Secret: {client_info['client_secret'][:8]}...")
            return client_info
        else:
            logger.error(f"OAuth client registration failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error registering OAuth client: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Check OAuth setup in deployed environment')
    parser.add_argument('--mcp-url', required=True, help='URL of the MCP server')
    parser.add_argument('--django-url', required=True, help='URL of the Django client')
    parser.add_argument('--admin-username', default='admin', help='Admin username for MCP server')
    parser.add_argument('--admin-password', help='Admin password for MCP server')
    args = parser.parse_args()
    
    # Check MCP server health
    if not check_mcp_server(args.mcp_url):
        logger.error("MCP server health check failed. Aborting.")
        return 1
    
    # Check Django client health and get OAuth info
    oauth_info = check_django_client(args.django_url)
    
    if not oauth_info:
        logger.error("Could not retrieve OAuth information from Django client. Aborting.")
        return 1
    
    # Check if using default credentials
    if oauth_info.get('using_default_credentials', True):
        logger.warning("Django client is using default OAuth credentials!")
    
    # Check client registration with MCP server
    client_id = oauth_info.get('client_id')
    if client_id:
        client_registered = check_client_registration(args.mcp_url, client_id)
        
        if not client_registered:
            logger.error(f"Client ID {client_id} is not registered with the MCP server.")
            
            # If admin password is provided, attempt to register a new client
            if args.admin_password:
                logger.info("Attempting to register a new OAuth client...")
                redirect_uri = f"{args.django_url}/oauth/callback"
                new_client = register_new_client(
                    args.mcp_url, 
                    args.admin_username, 
                    args.admin_password, 
                    redirect_uri
                )
                
                if new_client:
                    logger.info("Successfully registered a new OAuth client.")
                    logger.info("You can update the Django client's environment variables with these credentials:")
                    logger.info(f"OAUTH_CLIENT_ID={new_client['client_id']}")
                    logger.info(f"OAUTH_CLIENT_SECRET={new_client['client_secret']}")
                else:
                    logger.error("Failed to register a new OAuth client.")
            else:
                logger.info("Provide --admin-password to attempt registering a new client.")
        else:
            logger.info(f"Client ID {client_id} is properly registered with the MCP server.")
    else:
        logger.error("No client ID found in Django client's OAuth information.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
