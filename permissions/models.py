"""Models for the permissions app."""
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
from uuid import UUID

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ContextPermission(models.Model):
    """
    Manages permissions for accessing context blocks.
    
    This model defines what level of access different entities have to specific
    context blocks. It supports different permission scopes and can be time-limited.
    
    Attributes:
        id: A unique identifier for the permission (UUID).
        context_block: The context block this permission applies to.
        accessor_id: Identifier of the entity (user, agent, or system) with access.
        scope: The level of access granted (full, anonymized, or vector only).
        expires_at: When this permission expires (optional).
        created_at: When the permission was created.
    """
    
    class PermissionScope(models.TextChoices):
        """Available permission scopes for context blocks."""
        FULL = 'full', _('Full Access')
        ANONYMIZED = 'anonymized', _('Anonymized Access')
        VECTOR_ONLY = 'vector_only', _('Vector Only')
    
    id = models.UUIDField(
        primary_key=True,
        help_text=_("A unique identifier for the permission")
    )
    
    context_block = models.ForeignKey(
        'memories.ContextBlock',
        on_delete=models.CASCADE,
        related_name='permissions',
        help_text=_("The context block this permission applies to")
    )
    
    accessor_id = models.CharField(
        max_length=100,
        help_text=_(
            "Identifier of the entity (user, agent, or system) with access. "
            "Use 'public' for public access or 'authenticated' for any authenticated user."
        )
    )
    
    scope = models.CharField(
        max_length=20,
        choices=PermissionScope.choices,
        help_text=_("The level of access granted")
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When this permission expires (leave blank for no expiration)")
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        help_text=_("When the permission was created")
    )
    
    class Meta:
        """Metadata options for the ContextPermission model."""
        ordering = ['-created_at']
        verbose_name = _('Context Permission')
        verbose_name_plural = _('Context Permissions')
        indexes = [
            models.Index(fields=['accessor_id']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['context_block', 'accessor_id'],
                name='unique_permission_per_accessor'
            )
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the permission."""
        return f"{self.accessor_id} - {self.get_scope_display()} - {self.context_block}"
    
    def is_expired(self) -> bool:
        """Check if this permission has expired."""
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at
    
    def is_active(self) -> bool:
        """Check if this permission is currently active (not expired)."""
        return not self.is_expired()
    
    def allows_full_access(self) -> bool:
        """Check if this permission grants full access to the content."""
        return self.scope == self.PermissionScope.FULL and self.is_active()
    
    def allows_anonymized_access(self) -> bool:
        """Check if this permission allows anonymized access to the content."""
        return self.scope in [
            self.PermissionScope.FULL,
            self.PermissionScope.ANONYMIZED
        ] and self.is_active()
    
    def allows_vector_access(self) -> bool:
        """Check if this permission allows vector-based access to the content."""
        return self.is_active()  # All active permissions allow vector access
    
    @classmethod
    def get_effective_permission(
        cls,
        context_block_id: UUID,
        accessor_id: str
    ) -> Optional['ContextPermission']:
        """
        Get the most permissive non-expired permission for a context block and accessor.
        
        Args:
            context_block_id: The ID of the context block
            accessor_id: The ID of the accessor
            
        Returns:
            The most permissive active permission, or None if no valid permission exists
        """
        # First try to get a direct permission
        permission = cls.objects.filter(
            context_block_id=context_block_id,
            accessor_id=accessor_id,
            expires_at__gt=timezone.now()
        ).order_by('-scope').first()
        
        # If no direct permission, check for public access
        if not permission and accessor_id != 'public':
            return cls.get_effective_permission(context_block_id, 'public')
            
        return permission if (permission and permission.is_active()) else None
