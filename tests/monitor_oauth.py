#!/usr/bin/env python
"""
OAuth Credential Monitoring Script for Render Deployments

This script checks the status of OAuth credentials between the Django client
and MCP server, verifying the credentials are synchronized and valid.

Usage:
    python monitor_oauth.py --django-url DJANGO_URL --mcp-url MCP_URL --admin-password PASSWORD

Example:
    python monitor_oauth.py --django-url https://picard-django-client.onrender.com \
                           --mcp-url https://picard-mcp-server.onrender.com \
                           --admin-password adminpassword
"""
import argparse
import requests
import json
import sys
import time
import base64
import logging
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('oauth_monitor.log')
    ]
)

logger = logging.getLogger('oauth_monitor')

def check_client_info(mcp_url, client_id):
    """Check if the client ID exists on the MCP server using the client_info endpoint."""
    url = urljoin(mcp_url, f"/api/oauth/client_info?client_id={client_id}")
    logger.info(f"Checking client info for {client_id} at {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            client_info = response.json()
            logger.info(f"Client validated: {client_info['client_name']}")
            return True, client_info
        else:
            logger.warning(f"Client validation failed: {response.status_code} - {response.text}")
            return False, None
    except requests.RequestException as e:
        logger.error(f"Error connecting to MCP server: {e}")
        return False, None

def check_django_health(django_url):
    """Check if the Django client is healthy and get its OAuth status."""
    url = urljoin(django_url, "/health/")
    logger.info(f"Checking Django health at {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            logger.info(f"Django health: {health_data}")
            
            # Check if OAuth info is included
            if 'oauth' in health_data:
                oauth_info = health_data['oauth']
                logger.info(f"OAuth client ID: {oauth_info.get('client_id', 'Not configured')}")
                return True, oauth_info
            else:
                logger.warning("No OAuth information in health check response")
                return True, None
        else:
            logger.warning(f"Django health check failed: {response.status_code}")
            return False, None
    except requests.RequestException as e:
        logger.error(f"Error connecting to Django client: {e}")
        return False, None

def list_oauth_clients(mcp_url, admin_username, admin_password):
    """List all OAuth clients registered on the MCP server."""
    url = urljoin(mcp_url, "/api/admin/clients")
    logger.info(f"Listing OAuth clients at {url}")
    
    auth = (admin_username, admin_password)
    
    try:
        response = requests.get(url, auth=auth, timeout=10)
        
        if response.status_code == 200:
            clients = response.json()
            logger.info(f"Found {len(clients)} OAuth clients")
            return clients
        else:
            logger.warning(f"Failed to list OAuth clients: {response.status_code} - {response.text}")
            return None
    except requests.RequestException as e:
        logger.error(f"Error connecting to MCP server: {e}")
        return None

def trigger_oauth_fix(django_url, admin_username, admin_password):
    """
    Trigger the ensure_oauth_credentials command on the Django client.
    
    This is a more direct approach than calling the management command directly.
    It requires an admin endpoint that we might need to add to the Django client.
    """
    url = urljoin(django_url, "/admin/fix-oauth/")
    logger.info(f"Triggering OAuth fix at {url}")
    
    auth = (admin_username, admin_password)
    
    try:
        response = requests.post(url, auth=auth, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"OAuth fix triggered: {result}")
            return True
        else:
            logger.warning(f"Failed to trigger OAuth fix: {response.status_code} - {response.text}")
            return False
    except requests.RequestException as e:
        logger.error(f"Error connecting to Django client: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Monitor OAuth credentials between Django client and MCP server')
    parser.add_argument('--django-url', required=True, help='URL of the Django client')
    parser.add_argument('--mcp-url', required=True, help='URL of the MCP server')
    parser.add_argument('--admin-username', default='admin', help='Admin username')
    parser.add_argument('--admin-password', required=True, help='Admin password')
    parser.add_argument('--fix', action='store_true', help='Attempt to fix OAuth credentials if validation fails')
    
    args = parser.parse_args()
    
    logger.info("Starting OAuth credential monitoring")
    
    # Check Django health and get OAuth client ID
    django_healthy, oauth_info = check_django_health(args.django_url)
    
    if not django_healthy:
        logger.error("Django client is not healthy. Exiting.")
        sys.exit(1)
    
    if not oauth_info:
        logger.warning("No OAuth information available. Django client may not be properly configured.")
        
        if args.fix:
            logger.info("Attempting to fix OAuth credentials...")
            fixed = trigger_oauth_fix(args.django_url, args.admin_username, args.admin_password)
            
            if fixed:
                logger.info("OAuth credentials fixed. Waiting for changes to take effect...")
                time.sleep(5)
                django_healthy, oauth_info = check_django_health(args.django_url)
            else:
                logger.error("Failed to fix OAuth credentials. Manual intervention required.")
                sys.exit(1)
    
    # If we have a client ID, validate it with MCP server
    if oauth_info and 'client_id' in oauth_info:
        client_id = oauth_info['client_id']
        valid, client_info = check_client_info(args.mcp_url, client_id)
        
        if valid:
            logger.info("OAuth credentials are valid and synchronized between Django client and MCP server.")
            logger.info(f"Client name: {client_info['client_name']}")
            logger.info(f"Redirect URIs: {', '.join(client_info['redirect_uris'])}")
            logger.info(f"Scopes: {', '.join(client_info['scopes'])}")
            
            # Successful validation
            sys.exit(0)
        else:
            logger.warning("OAuth client ID exists in Django but is not valid in MCP server.")
            
            if args.fix:
                logger.info("Attempting to fix OAuth credentials...")
                fixed = trigger_oauth_fix(args.django_url, args.admin_username, args.admin_password)
                
                if fixed:
                    logger.info("OAuth credentials fixed. Run this script again to verify.")
                else:
                    logger.error("Failed to fix OAuth credentials. Manual intervention required.")
                
                sys.exit(1)
    else:
        logger.warning("No client ID available. Django client may not be properly configured.")
        sys.exit(1)

if __name__ == "__main__":
    main()
