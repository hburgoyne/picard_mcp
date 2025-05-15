from django.db import models

class EmbeddingLog(models.Model):
    """Model for tracking embedding generation."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('complete', 'Complete'),
        ('error', 'Error'),
    ]
    
    id = models.UUIDField(primary_key=True)
    context_block = models.OneToOneField(
        'memories.ContextBlock',
        on_delete=models.CASCADE,
        related_name='embedding_log'
    )
    embedding_method = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.context_block} - {self.get_status_display()}"
