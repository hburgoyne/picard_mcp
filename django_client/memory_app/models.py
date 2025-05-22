from django.db import models
from django.contrib.auth.models import User
import uuid
from datetime import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver

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
        
    @classmethod
    def get_for_user(cls, user):
        """Get the OAuth token for a user.
        
        Args:
            user: The user to get the token for.
            
        Returns:
            The OAuthToken instance for the user, or None if no token exists.
        """
        try:
            return cls.objects.get(user=user)
        except cls.DoesNotExist:
            return None

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

class UserProfile(models.Model):
    """Model for storing additional user information."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.CharField(max_length=255, blank=True, null=True)  # URL to profile picture
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile instance when a User is created."""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile instance when the User is saved."""
    instance.profile.save()
