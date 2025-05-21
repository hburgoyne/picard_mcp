from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from pgvector.sqlalchemy import Vector

from app.models.base import BaseModel

class Memory(BaseModel):
    """Memory model for storing user memories with vector embeddings."""
    __tablename__ = "memories"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    encrypted_text = Column(Text, nullable=True)  # For storing encrypted version of the text
    permission = Column(String, nullable=False, default="private")  # private, public
    embedding = Column(Vector(1536), nullable=True)  # Vector embedding for semantic search
    expiration_date = Column(DateTime, nullable=True)  # When the memory expires
    
    # Relationships
    user = relationship("User", back_populates="memories")
    
    @property
    def is_expired(self):
        """Check if the memory has expired."""
        if self.expiration_date is None:
            return False
        return datetime.utcnow() > self.expiration_date
