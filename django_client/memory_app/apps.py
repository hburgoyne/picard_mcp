from django.apps import AppConfig
import os
import logging

logger = logging.getLogger(__name__)

class MemoryAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'memory_app'
    
    def ready(self):
        """Called when Django starts up."""
        # Only run OAuth credential check when explicitly enabled
        try:
            from django.conf import settings
            if getattr(settings, 'ENSURE_OAUTH_CREDENTIALS', False):
                logger.info("ENSURE_OAUTH_CREDENTIALS enabled - checking OAuth credentials")
                self.ensure_oauth_credentials()
        except Exception as e:
            logger.warning(f"Failed to ensure OAuth credentials: {e}")
    
    def ensure_oauth_credentials(self):
        """Ensure OAuth credentials are properly configured."""
        try:
            from django.conf import settings
            from django.core.management import call_command
            
            logger.info("Running OAuth credentials check...")
            call_command('ensure_oauth_credentials')
        except Exception as e:
            logger.error(f"Failed to ensure OAuth credentials: {e}")
        
        # Check if we're using default credentials
        using_defaults = (
            getattr(settings, 'OAUTH_CLIENT_ID', '') == '550e8400-e29b-41d4-a716-446655440000' or 
            getattr(settings, 'OAUTH_CLIENT_SECRET', '') == 'a_strong_random_secret_at_least_32_characters'
        )
        
        if using_defaults:
            logger.info("Default OAuth credentials detected - attempting to register new client")
            try:
                call_command('ensure_oauth_credentials')
            except Exception as e:
                logger.error(f"Failed to ensure OAuth credentials: {e}")
