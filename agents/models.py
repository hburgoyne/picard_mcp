from django.db import models
from django.conf import settings

class Agent(models.Model):
    """Model representing an MCP agent."""
    id = models.UUIDField(primary_key=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='agents'
    )
    name = models.CharField(max_length=255)
    purpose = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.owner.email})"
