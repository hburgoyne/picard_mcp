from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.database import Base

class OAuthClient(Base):
    """OAuth client model for storing client information"""
    __tablename__ = "oauth_clients"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, unique=True, index=True, nullable=False)
    client_secret = Column(String, nullable=False)
    redirect_uris = Column(ARRAY(String), nullable=False)
    allowed_scopes = Column(ARRAY(String), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tokens = relationship("OAuthToken", back_populates="client", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert client to dictionary"""
        return {
            "id": self.id,
            "client_id": self.client_id,
            "redirect_uris": self.redirect_uris,
            "allowed_scopes": self.allowed_scopes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

class OAuthToken(Base):
    """OAuth token model for storing token information"""
    __tablename__ = "oauth_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(String, unique=True, index=True, nullable=False)
    refresh_token = Column(String, unique=True, index=True, nullable=True)
    token_type = Column(String, default="bearer", nullable=False)
    scopes = Column(ARRAY(String), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("oauth_clients.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="oauth_tokens")
    client = relationship("OAuthClient", back_populates="tokens")
    
    def to_dict(self):
        """Convert token to dictionary"""
        return {
            "id": self.id,
            "access_token": self.access_token,
            "token_type": self.token_type,
            "scopes": self.scopes,
            "expires_at": self.expires_at.isoformat(),
            "user_id": self.user_id,
            "client_id": self.client_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
