"""
MCP Server API client utilities.
"""
import requests
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from memory_app.models import OAuthToken

logger = logging.getLogger(__name__)

def connect_user_to_mcp_server(user):
    """
    Connect a Django user to the MCP server without direct user authentication.
    
    This uses the user-token endpoint to either find or create a corresponding user
    on the MCP server and obtain tokens for that user.
    
    Args:
        user: Django User instance
        
    Returns:
        OAuthToken instance if successful, None otherwise
    """
    try:
        # Prepare token request
        token_data = {
            'client_id': settings.OAUTH_CLIENT_ID,
            'client_secret': settings.OAUTH_CLIENT_SECRET,
            'username': user.username,
            'email': user.email,
            'create_if_not_exists': 'true'  # Form data needs string values
        }
        
        # Use the internal URL for server-to-server communication within Docker
        token_url = f"{settings.MCP_SERVER_INTERNAL_URL}/api/user-tokens/user-token"
        logger.info(f"Requesting user token from: {token_url}")
        
        # Send the request
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        token_info = response.json()
        
        # Calculate token expiration
        expires_in = token_info.get('expires_in', 3600)  # Default to 1 hour
        expires_at = timezone.now() + timedelta(seconds=expires_in)
        
        # Save tokens to database
        oauth_token, created = OAuthToken.objects.update_or_create(
            user=user,
            defaults={
                'access_token': token_info['access_token'],
                'refresh_token': token_info['refresh_token'],
                'expires_at': expires_at,
                'scope': token_info['scope'],
            }
        )
        
        logger.info(f"Successfully connected user {user.username} to MCP server")
        return oauth_token
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting user to MCP server: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response content: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error connecting user to MCP server: {str(e)}")
        return None
