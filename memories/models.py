from django.db import models
from django.conf import settings

class ContextBlock(models.Model):
    """Model for storing MCP context blocks."""
    CONTEXT_TYPES = [
        ('belief', 'Belief'),
        ('value', 'Value'),
        ('preference', 'Preference'),
        ('position', 'Position'),
    ]
    
    id = models.UUIDField(primary_key=True)
    agent = models.ForeignKey(
        'agents.Agent',
        on_delete=models.CASCADE,
        related_name='context_blocks'
    )
    namespace = models.CharField(max_length=100)
    tag = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=CONTEXT_TYPES)
    content = models.TextField()
    source = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.agent.name} - {self.namespace}.{self.tag}"
