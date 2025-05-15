"""Models for the memories app."""
from typing import Dict, List, Optional, Tuple, Union
from uuid import UUID

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ContextBlock(models.Model):
    """
    Represents a context block that stores a piece of information or memory.
    
    Context blocks are the fundamental unit of memory in the MCP system.
    They can represent beliefs, values, preferences, or positions that an agent holds.
    
    Attributes:
        CONTEXT_TYPES: Choices for the type of context block.
        id: A unique identifier for the context block (UUID).
        agent: The agent this context block belongs to.
        namespace: A category or domain for the context block.
        tag: A unique identifier within the namespace.
        type: The type of context (belief, value, preference, position).
        content: The actual content of the context block.
        source: The origin of this context block.
        created_at: When the context block was created.
        updated_at: When the context block was last updated.
    """
    
    class ContextType(models.TextChoices):
        """Possible types of context blocks."""
        BELIEF = 'belief', _('Belief')
        VALUE = 'value', _('Value')
        PREFERENCE = 'preference', _('Preference')
        POSITION = 'position', _('Position')
    
    id = models.UUIDField(
        primary_key=True,
        help_text=_("A unique identifier for the context block")
    )
    
    agent = models.ForeignKey(
        'agents.Agent',
        on_delete=models.CASCADE,
        related_name='context_blocks',
        help_text=_("The agent this context block belongs to")
    )
    
    namespace = models.CharField(
        max_length=100,
        help_text=_("A category or domain for the context block")
    )
    
    tag = models.CharField(
        max_length=100,
        help_text=_("A unique identifier within the namespace")
    )
    
    type = models.CharField(
        max_length=20,
        choices=ContextType.choices,
        help_text=_("The type of context (belief, value, preference, position)")
    )
    
    content = models.TextField(
        help_text=_("The actual content of the context block")
    )
    
    source = models.CharField(
        max_length=100,
        help_text=_("The origin of this context block")
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        help_text=_("When the context block was created")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("When the context block was last updated")
    )
    
    class Meta:
        """Metadata options for the ContextBlock model."""
        ordering = ['-created_at']
        verbose_name = _('Context Block')
        verbose_name_plural = _('Context Blocks')
        indexes = [
            models.Index(fields=['agent', 'namespace', 'tag']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            models.Index(fields=['type']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['agent', 'namespace', 'tag'],
                name='unique_namespace_tag_per_agent'
            )
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the context block."""
        return f"{self.agent.name} - {self.namespace}.{self.tag} ({self.get_type_display()})"
    
    def get_embedding(self):
        """Get the embedding for this context block if it exists."""
        try:
            return self.embedding_log.embedding
        except EmbeddingLog.DoesNotExist:
            return None
    
    def has_public_permission(self) -> bool:
        """Check if this context block has any public permissions."""
        return self.permissions.filter(
            scope='public',
            expires_at__isnull=True
        ).exists()
    
    def get_permission_scopes(self) -> List[str]:
        """Get all unique permission scopes for this context block."""
        return list(
            self.permissions.filter(
                expires_at__isnull=True
            ).values_list('scope', flat=True).distinct()
        )


# Add this at the bottom to avoid circular imports
from embeddings.models import EmbeddingLog  # noqa
