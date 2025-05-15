from django.db import models

class ContextPermission(models.Model):
    """Model for managing permissions on context blocks."""
    PERMISSION_SCOPES = [
        ('full', 'Full Access'),
        ('anonymized', 'Anonymized Access'),
        ('vector_only', 'Vector Only'),
    ]
    
    id = models.UUIDField(primary_key=True)
    context_block = models.ForeignKey(
        'memories.ContextBlock',
        on_delete=models.CASCADE,
        related_name='permissions'
    )
    accessor_id = models.CharField(max_length=100)
    scope = models.CharField(max_length=20, choices=PERMISSION_SCOPES)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.accessor_id} - {self.get_scope_display()} - {self.context_block}"
