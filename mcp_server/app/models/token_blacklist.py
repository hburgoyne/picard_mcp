"""
Token blacklist model for OAuth token revocation.
"""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.models.base import BaseModel

class TokenBlacklist(BaseModel):
    """Token blacklist model for revoking OAuth tokens."""
    __tablename__ = "token_blacklist"
    
    token_jti = Column(String, nullable=False, index=True)
    blacklisted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reason = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    
    @classmethod
    def is_blacklisted(cls, db, token_jti):
        """
        Check if a token is blacklisted.
        
        Args:
            db: Database session
            token_jti: Token identifier
            
        Returns:
            True if token is blacklisted, False otherwise
        """
        token = db.query(cls).filter(cls.token_jti == token_jti).first()
        
        # Clean up expired blacklisted tokens
        if token and datetime.utcnow() > token.expires_at:
            db.delete(token)
            db.commit()
            return False
            
        return token is not None
