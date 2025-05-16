from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from pgvector.sqlalchemy import Vector

from app.database import Base

class MemoryPermission(str, Enum):
    """Memory permission types"""
    PRIVATE = "private"
    PUBLIC = "public"

class Memory(Base):
    """Memory model for storing user memories with vector embeddings"""
    __tablename__ = "memories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(1536))  # OpenAI embeddings are 1536 dimensions
    permission = Column(String, default=MemoryPermission.PRIVATE.value, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="memories")
    
    def to_dict(self):
        """Convert memory to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "text": self.text,
            "permission": self.permission,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
