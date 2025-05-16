from django.db import models
from django.contrib.auth.models import User


class OAuthToken(models.Model):
    """Model to store OAuth tokens for users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='oauth_token')
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_at = models.DateTimeField()
    scope = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Token for {self.user.username}"
