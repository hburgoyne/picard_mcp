from django.http import JsonResponse
from django.db import connection
from django.db.utils import OperationalError
from django.conf import settings
import requests
import logging

from .models import OAuthToken

logger = logging.getLogger(__name__)

def health_check(request):
    """Health check endpoint for the Django client."""
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"
    except OperationalError:
        db_status = "unhealthy"
    
    # Check OAuth status
    oauth_status = check_oauth_status()
    
    # Return health status
    return JsonResponse({
        "status": "healthy",
        "database": db_status,
        "service": "django_client",
        "oauth": oauth_status
    })

def check_oauth_status():
    """Check the status of OAuth credentials and connection to MCP server."""
    oauth_status = {
        "client_id": settings.OAUTH_CLIENT_ID,
        "using_default_credentials": settings.USING_DEFAULT_OAUTH_CREDENTIALS,
        "configured": not settings.USING_DEFAULT_OAUTH_CREDENTIALS,
        "tokens_exist": False,
        "mcp_validated": False
    }
    
    # Check if any tokens exist in the database
    token_count = OAuthToken.objects.count()
    oauth_status["tokens_exist"] = token_count > 0
    oauth_status["token_count"] = token_count
    
    # Try to validate client ID with MCP server
    if not settings.USING_DEFAULT_OAUTH_CREDENTIALS:
        try:
            mcp_server_url = getattr(settings, 'MCP_SERVER_INTERNAL_URL', None) or \
                            getattr(settings, 'MCP_SERVER_URL', 'http://mcp_server:8000')
            
            # Use the client_info endpoint to validate the client ID
            url = f"{mcp_server_url}/api/oauth/client_info?client_id={settings.OAUTH_CLIENT_ID}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                client_info = response.json()
                oauth_status["mcp_validated"] = True
                oauth_status["client_name"] = client_info.get("client_name", "Unknown")
                oauth_status["redirect_uris"] = client_info.get("redirect_uris", [])
            else:
                oauth_status["mcp_validation_error"] = f"Status code: {response.status_code}"
        except Exception as e:
            oauth_status["mcp_validation_error"] = str(e)
    
    return oauth_status
