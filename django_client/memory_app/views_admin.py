"""
Admin views for OAuth credential management.

These views allow administrators to manage OAuth credentials and fix issues remotely.
"""

from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
import logging
import base64
import os

logger = logging.getLogger(__name__)

def is_admin(user):
    """Check if user is a superuser or has the admin flag set."""
    return user.is_superuser

@csrf_exempt
@require_POST
@user_passes_test(is_admin)
def fix_oauth_credentials(request):
    """
    Force the renewal of OAuth credentials.
    
    This endpoint allows administrators to trigger the ensure_oauth_credentials
    management command with the --force flag to regenerate credentials.
    
    This is useful for remote diagnostics and fixing deployment issues.
    """
    logger.info("Admin triggered OAuth credential fix")
    
    try:
        # Run the command with force flag
        call_command('ensure_oauth_credentials', force=True)
        
        return JsonResponse({
            'status': 'success',
            'message': 'OAuth credentials have been regenerated',
            'client_id': settings.OAUTH_CLIENT_ID,
            'using_default_credentials': settings.USING_DEFAULT_OAUTH_CREDENTIALS
        })
    except Exception as e:
        logger.error(f"Error fixing OAuth credentials: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_POST
def fix_oauth_credentials_basic_auth(request):
    """
    Force the renewal of OAuth credentials using basic auth.
    
    This endpoint is similar to fix_oauth_credentials but uses HTTP Basic Auth
    instead of Django's authentication system. This is useful for automated
    scripts and monitoring tools.
    """
    # Check for basic auth header
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Basic '):
        return JsonResponse({
            'status': 'error',
            'message': 'Basic authentication required'
        }, status=401)
    
    # Decode and verify credentials
    try:
        auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
        username, password = auth_decoded.split(':', 1)
        
        # Check credentials against environment variables
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        
        if not admin_password or username != admin_username or password != admin_password:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid credentials'
            }, status=401)
        
        # Authenticated successfully, run the command
        logger.info(f"Admin {username} triggered OAuth credential fix via basic auth")
        call_command('ensure_oauth_credentials', force=True)
        
        return JsonResponse({
            'status': 'success',
            'message': 'OAuth credentials have been regenerated',
            'client_id': settings.OAUTH_CLIENT_ID,
            'using_default_credentials': settings.USING_DEFAULT_OAUTH_CREDENTIALS
        })
    except Exception as e:
        logger.error(f"Error in fix_oauth_credentials_basic_auth: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
