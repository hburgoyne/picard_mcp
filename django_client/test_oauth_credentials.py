"""
Simple script to test the OAuth credential validation and registration.

This script helps diagnose issues with the OAuth credential management
by testing each component separately.
"""
import os
import sys
import logging
import time
import requests
import json
import base64
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('oauth_test')

def main():
    """Run the test script."""
    # Get MCP server URL from environment or use default
    mcp_server_url = os.environ.get('MCP_SERVER_URL', 'http://localhost:8001')
    client_id = os.environ.get('OAUTH_CLIENT_ID')
    
    if not client_id:
        logger.error("No OAUTH_CLIENT_ID set in environment")
        return 1
    
    # Test client_info endpoint
    logger.info(f"Testing client_info endpoint for client ID: {client_id}")
    try:
        response = requests.get(
            f"{mcp_server_url}/api/oauth/client_info?client_id={client_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            client_info = response.json()
            logger.info(f"Client validation successful: {client_info}")
            logger.info("OAuth credentials are valid and properly configured.")
            return 0
        else:
            logger.error(f"Client validation failed: {response.status_code} - {response.text}")
            logger.error("OAuth credentials are invalid or improperly configured.")
            return 1
    except Exception as e:
        logger.error(f"Error testing client_info endpoint: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
