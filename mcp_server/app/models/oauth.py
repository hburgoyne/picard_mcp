from sqlalchemy import Column, String, ForeignKey, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timedelta

from app.models.base import BaseModel
from app.core.config import settings

class OAuthClient(BaseModel):
    """OAuth client model for client registration."""
    __tablename__ = "oauth_clients"
    
    client_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    client_secret = Column(String, nullable=False)
    client_name = Column(String, nullable=False)
    redirect_uris = Column(ARRAY(String), nullable=False)
    scopes = Column(ARRAY(String), nullable=False)
    is_confidential = Column(Boolean, default=True)
    grant_types = Column(ARRAY(String), nullable=True)
    response_types = Column(ARRAY(String), nullable=True)
    client_uri = Column(String, nullable=True)
    logo_uri = Column(String, nullable=True)
    tos_uri = Column(String, nullable=True)
    policy_uri = Column(String, nullable=True)
    jwks_uri = Column(String, nullable=True)
    software_id = Column(String, nullable=True)
    software_version = Column(String, nullable=True)
    
    # Relationships
    authorization_codes = relationship("AuthorizationCode", back_populates="client", cascade="all, delete-orphan")
    tokens = relationship("Token", back_populates="client", cascade="all, delete-orphan")

class AuthorizationCode(BaseModel):
    """Authorization code model for OAuth authorization flow."""
    __tablename__ = "authorization_codes"
    
    code = Column(String, nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("oauth_clients.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    redirect_uri = Column(String, nullable=False)
    scope = Column(String, nullable=False)
    expires_at = Column(String, nullable=False)
    code_challenge = Column(String, nullable=True)
    code_challenge_method = Column(String, nullable=True)
    
    # Relationships
    client = relationship("OAuthClient", back_populates="authorization_codes")
    user = relationship("User")
    
    @property
    def is_expired(self):
        """Check if the authorization code has expired."""
        return datetime.utcnow() > datetime.fromisoformat(self.expires_at)

class Token(BaseModel):
    """Token model for OAuth access and refresh tokens."""
    __tablename__ = "tokens"
    
    access_token = Column(String, nullable=False, index=True)
    refresh_token = Column(String, nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("oauth_clients.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    scope = Column(String, nullable=False)
    access_token_expires_at = Column(String, nullable=False)
    refresh_token_expires_at = Column(String, nullable=False)
    is_revoked = Column(Boolean, default=False)
    
    # Relationships
    client = relationship("OAuthClient", back_populates="tokens")
    user = relationship("User")
    
    @property
    def is_access_token_expired(self):
        """Check if the access token has expired."""
        return datetime.utcnow() > datetime.fromisoformat(self.access_token_expires_at)
    
    @property
    def is_refresh_token_expired(self):
        """Check if the refresh token has expired."""
        return datetime.utcnow() > datetime.fromisoformat(self.refresh_token_expires_at)
