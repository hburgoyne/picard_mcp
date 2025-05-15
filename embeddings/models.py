"""Models for the embeddings app."""
from typing import Dict, List, Optional, Tuple, Union
from uuid import UUID

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from pgvector.django import VectorField


class EmbeddingLog(models.Model):
    """
    Tracks the generation and status of embeddings for context blocks.
    
    This model stores information about the embedding generation process,
    including the method used, status, any errors, and the actual vector
    representation of the context block's content.
    
    Attributes:
        id: A unique identifier for the embedding log entry.
        context_block: The context block this embedding is for.
        embedding: The vector representation of the context block.
        embedding_method: The method/algorithm used to generate the embedding.
        status: The current status of the embedding generation.
        error_message: Any error message if the generation failed.
        created_at: When the embedding was created.
        updated_at: When the embedding was last updated.
    """
    
    class Status(models.TextChoices):
        """Possible statuses for embedding generation."""
        PENDING = 'pending', _('Pending')
        COMPLETE = 'complete', _('Complete')
        ERROR = 'error', _('Error')
    
    id = models.UUIDField(
        primary_key=True,
        help_text=_("A unique identifier for the embedding log entry")
    )
    
    context_block = models.OneToOneField(
        'memories.ContextBlock',
        on_delete=models.CASCADE,
        related_name='embedding_log',
        help_text=_("The context block this embedding is for")
    )
    
    # Vector field for storing the embedding (dimension should match your embedding model)
    embedding = VectorField(
        dimensions=384,  # Adjust based on your embedding model
        null=True,
        blank=True,
        help_text=_("The vector representation of the context block")
    )
    
    embedding_method = models.CharField(
        max_length=100,
        help_text=_("The method/algorithm used to generate the embedding")
    )
    
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_("The current status of the embedding generation")
    )
    
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text=_("Any error message if the generation failed")
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        help_text=_("When the embedding was created")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("When the embedding was last updated")
    )
    
    class Meta:
        """Metadata options for the EmbeddingLog model."""
        ordering = ['-created_at']
        verbose_name = _('Embedding Log')
        verbose_name_plural = _('Embedding Logs')
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            models.Index(fields=['embedding'], name='embedding_vector_index', opclasses=['vector_l2_ops']),
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the embedding log."""
        return f"{self.context_block} - {self.get_status_display()}"
    
    def get_embedding_dimensions(self) -> int:
        """Get the dimensions of the embedding vector."""
        if not self.embedding:
            return 0
        return len(self.embedding)
    
    def is_ready(self) -> bool:
        """Check if the embedding is ready to use."""
        return self.status == self.Status.COMPLETE and self.embedding is not None
    
    def get_similar_context_blocks(self, threshold: float = 0.7, limit: int = 5):
        """
        Find similar context blocks based on vector similarity.
        
        Args:
            threshold: Minimum similarity score (0-1)
            limit: Maximum number of results to return
            
        Returns:
            QuerySet of similar ContextBlock instances
        """
        if not self.is_ready():
            return self.context_block.__class__.objects.none()
            
        from django.db.models.functions import Least
        
        # Using vector distance operator (<=>) for similarity search
        # The similarity is calculated as 1 - (distance between vectors)
        return (
            self.context_block.__class__.objects
            .exclude(id=self.context_block_id)
            .filter(
                embedding_log__embedding__isnull=False,
                embedding_log__status=self.Status.COMPLETE
            )
            .annotate(
                similarity=models.Value(1.0) - models.F('embedding_log__embedding').l2_distance(self.embedding)
            )
            .filter(similarity__gte=threshold)
            .order_by('-similarity')[:limit]
        )
