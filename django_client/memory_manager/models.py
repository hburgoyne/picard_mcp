from django.db import models
from django.contrib.auth.models import User


class Memory(models.Model):
    """Model to store memories"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memories')
    memory_id = models.CharField(max_length=255, unique=True)
    text = models.TextField()
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Memories"
        ordering = ['-created_at']

    def __str__(self):
        return f"Memory {self.memory_id} by {self.user.username}"
