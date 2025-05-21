from django.db import models
from django.contrib.auth.models import User
import uuid
from datetime import datetime

class OAuthToken(models.Model):
    """Model to store OAuth tokens for MCP server."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='oauth_token')
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.DateTimeField()
    scope = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_expired(self):
        """Check if the access token has expired."""
        return datetime.now().astimezone() > self.expires_at

class Memory(models.Model):
    """Model to store local copies of memories from the MCP server."""
    PERMISSION_CHOICES = [
        ('private', 'Private'),
        ('public', 'Public'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memories')
    text = models.TextField()
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default='private')
    expiration_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    
    @property
    def is_expired(self):
        """Check if the memory has expired."""
        if self.expiration_date is None:
            return False
        return datetime.now().astimezone() > self.expiration_date
    
    class Meta:
        verbose_name_plural = "Memories"
        ordering = ['-created_at']
