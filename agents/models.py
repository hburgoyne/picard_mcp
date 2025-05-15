"""Models for the agents app."""
from typing import Optional
from uuid import UUID

from django.conf import settings
from django.db import models
from django.utils import timezone


class Agent(models.Model):
    """
    Represents an MCP (Model Context Protocol) agent.
    
    An agent is a digital entity that can have its own set of memories,
    preferences, and behaviors. Each agent is owned by a user and can
    have multiple context blocks associated with it.
    
    Attributes:
        id: A unique identifier for the agent (UUID).
        owner: The user who owns this agent.
        name: The display name of the agent.
        purpose: A description of the agent's purpose or function.
        created_at: The timestamp when the agent was created.
    """
    id = models.UUIDField(
        primary_key=True,
        help_text="A unique identifier for the agent"
    )
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='agents',
        help_text="The user who owns this agent"
    )
    
    name = models.CharField(
        max_length=255,
        help_text="The display name of the agent"
    )
    
    purpose = models.TextField(
        blank=True,
        null=True,
        help_text="A description of the agent's purpose or function"
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        help_text="The timestamp when the agent was created"
    )
    
    class Meta:
        """Metadata options for the Agent model."""
        ordering = ['name']
        verbose_name = 'Agent'
        verbose_name_plural = 'Agents'
        indexes = [
            models.Index(fields=['owner', 'name']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'name'],
                name='unique_agent_name_per_owner'
            )
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the agent."""
        return f"{self.name} (ID: {self.id})"
    
    def get_context_blocks_count(self) -> int:
        """Return the number of context blocks associated with this agent."""
        return self.context_blocks.count()
    
    def get_public_context_blocks(self):
        """Return all public context blocks for this agent."""
        return self.context_blocks.filter(
            permissions__scope='public',
            permissions__expires_at__isnull=True
        ).distinct()
