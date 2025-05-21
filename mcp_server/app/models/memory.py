from sqlalchemy import Column, String, ForeignKey, DateTime, Text, ARRAY, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

# Use ARRAY(Float) instead of VECTOR since pgvector extension is handled separately
# The actual vector functionality comes from the pgvector extension

from app.models.base import BaseModel

class Memory(BaseModel):
    """Memory model for storing user memories with vector embeddings."""
    __tablename__ = "memories"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    encrypted_text = Column(Text, nullable=True)  # For storing encrypted version of the text
    permission = Column(String, nullable=False, default="private")  # private, public
    embedding = Column(ARRAY(Float), nullable=True)  # Vector embedding for semantic search (1536 dimensions)
    expiration_date = Column(DateTime, nullable=True)  # When the memory expires
    
    # Relationships
    user = relationship("User", back_populates="memories")
    
    @property
    def is_expired(self):
        """Check if the memory has expired."""
        if self.expiration_date is None:
            return False
        return datetime.utcnow() > self.expiration_date
