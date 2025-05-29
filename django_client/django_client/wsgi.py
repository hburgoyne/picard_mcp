import os
import sys
import logging

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_client.settings')

# Initialize application
application = get_wsgi_application()

# Ensure OAuth credentials on startup in production environment
if os.environ.get('ENSURE_OAUTH_CREDENTIALS') == 'true':
    try:
        logging.info("Ensuring OAuth credentials via WSGI startup")
        from django.core.management import call_command
        call_command('ensure_oauth_credentials')
    except Exception as e:
        logging.error(f"Failed to ensure OAuth credentials on WSGI startup: {e}")
