"""
OAuth 2.0 utility functions.
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import uuid
import hashlib
import base64
from typing import Tuple, Optional

from app.models.oauth import OAuthClient, AuthorizationCode, Token
from app.core.config import settings
from app.utils.logger import logger

class OAuthError(Exception):
    """Exception class for OAuth-specific errors."""
    def __init__(self, error: str, description: str):
        self.error = error
        self.description = description
        super().__init__(f"{error}: {description}")

def validate_client(db: Session, client_id: uuid.UUID) -> Optional[OAuthClient]:
    """
    Validate an OAuth client by client_id.
    
    Args:
        db: Database session
        client_id: OAuth client ID
        
    Returns:
        OAuthClient if valid, None otherwise
    """
    return db.query(OAuthClient).filter(OAuthClient.client_id == client_id).first()

def validate_redirect_uri(client: OAuthClient, redirect_uri: str) -> bool:
    """
    Validate that the redirect URI is registered for the client.
    
    Args:
        client: OAuth client
        redirect_uri: Redirect URI to validate
        
    Returns:
        True if valid, False otherwise
    """
    return redirect_uri in client.redirect_uris

def validate_client_credentials(client: OAuthClient, client_secret: str) -> bool:
    """
    Validate client credentials.
    
    Args:
        client: OAuth client
        client_secret: Client secret to validate
        
    Returns:
        True if valid, False otherwise
    """
    return client.client_secret == client_secret

def create_authorization_code(
    db: Session,
    client_id: uuid.UUID,
    user_id: uuid.UUID,
    redirect_uri: str,
    scope: str,
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = None
) -> str:
    """
    Create a new authorization code.
    
    Args:
        db: Database session
        client_id: OAuth client ID (this is the client_id field, not the id primary key)
        user_id: User ID
        redirect_uri: Redirect URI
        scope: Requested scopes
        code_challenge: PKCE code challenge
        code_challenge_method: PKCE code challenge method
        
    Returns:
        Authorization code string
    """
    # Find the client by client_id to get its primary key id
    client = db.query(OAuthClient).filter(OAuthClient.client_id == client_id).first()
    
    if not client:
        raise ValueError(f"No client found with client_id: {client_id}")
    
    # Generate a random code
    code = secrets.token_urlsafe(32)
    
    # Set expiration time (10 minutes)
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Create and store authorization code using the client's primary key id
    auth_code = AuthorizationCode(
        code=code,
        client_id=client.id,  # Use the primary key id, not the client_id field
        user_id=user_id,
        redirect_uri=redirect_uri,
        scope=scope,
        expires_at=expires_at.isoformat(),
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method
    )
    
    db.add(auth_code)
    db.commit()
    
    return code

def validate_authorization_code(
    db: Session,
    code: str,
    client_id: uuid.UUID,
    redirect_uri: str,
    code_verifier: Optional[str] = None
) -> AuthorizationCode:
    """
    Validate an authorization code.
    
    Args:
        db: Database session
        code: Authorization code
        client_id: OAuth client ID
        redirect_uri: Redirect URI
        code_verifier: PKCE code verifier
        
    Returns:
        AuthorizationCode if valid
        
    Raises:
        OAuthError: If validation fails
    """
    # Find the authorization code
    auth_code = db.query(AuthorizationCode).filter(
        AuthorizationCode.code == code,
        AuthorizationCode.client_id == client_id
    ).first()
    
    if not auth_code:
        raise OAuthError("invalid_grant", "Invalid authorization code")
    
    # Check if the authorization code has expired
    if auth_code.is_expired:
        db.delete(auth_code)
        db.commit()
        raise OAuthError("invalid_grant", "Authorization code has expired")
    
    # Verify redirect URI
    if auth_code.redirect_uri != redirect_uri:
        raise OAuthError("invalid_grant", "Redirect URI mismatch")
    
    # Verify PKCE code verifier if needed
    if auth_code.code_challenge and auth_code.code_challenge_method:
        if not code_verifier:
            raise OAuthError("invalid_grant", "Code verifier required")
            
        if auth_code.code_challenge_method == "S256":
            # Generate challenge from verifier
            hash_object = hashlib.sha256(code_verifier.encode())
            code_challenge = base64.urlsafe_b64encode(hash_object.digest()).decode().rstrip("=")
            
            # Compare with stored code challenge
            if code_challenge != auth_code.code_challenge:
                raise OAuthError("invalid_grant", "Code verifier does not match challenge")
    
    return auth_code

def create_access_token(
    db: Session,
    client_id: uuid.UUID,
    user_id: uuid.UUID,
    scope: str
) -> Tuple[str, str, int]:
    """
    Create access and refresh tokens.
    
    Args:
        db: Database session
        client_id: OAuth client ID (this is the client_id field, not the id primary key)
        user_id: User ID
        scope: Granted scopes
        
    Returns:
        Tuple of (access_token, refresh_token, expires_in)
    """
    # Find the client by client_id to get its primary key id
    client = db.query(OAuthClient).filter(OAuthClient.client_id == client_id).first()
    
    if not client:
        raise ValueError(f"No client found with client_id: {client_id}")
    
    # Generate random tokens
    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(32)
    
    # Set expiration times
    access_token_expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Create and store token using the client's primary key id
    token = Token(
        access_token=access_token,
        refresh_token=refresh_token,
        client_id=client.id,  # Use the primary key id, not the client_id field
        user_id=user_id,
        scope=scope,
        access_token_expires_at=access_token_expires_at.isoformat(),
        refresh_token_expires_at=refresh_token_expires_at.isoformat()
    )
    
    db.add(token)
    db.commit()
    
    # Return tokens and expiration
    return access_token, refresh_token, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

def validate_access_token(db: Session, token: str) -> Optional[Token]:
    """
    Validate an access token.
    
    Args:
        db: Database session
        token: Access token
        
    Returns:
        Token if valid, None otherwise
    """
    token_obj = db.query(Token).filter(Token.access_token == token).first()
    
    if not token_obj or token_obj.is_access_token_expired or token_obj.is_revoked:
        return None
        
    return token_obj

def refresh_access_token(
    db: Session, 
    refresh_token: str
) -> Optional[Tuple[str, str, int]]:
    """
    Refresh an access token using a refresh token.
    
    Args:
        db: Database session
        refresh_token: Refresh token
        
    Returns:
        Tuple of (new_access_token, new_refresh_token, expires_in) if valid,
        None otherwise
    """
    # Find the token by refresh token
    token_obj = db.query(Token).filter(Token.refresh_token == refresh_token).first()
    
    if not token_obj:
        return None
        
    # Check if refresh token has expired
    refresh_expires_at = datetime.fromisoformat(token_obj.refresh_token_expires_at)
    if datetime.utcnow() > refresh_expires_at:
        return None
    
    # Generate new access token and refresh token (token rotation)
    new_access_token = secrets.token_urlsafe(32)
    new_refresh_token = secrets.token_urlsafe(32)
    
    # Update expiration times
    access_token_expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Update token with new values
    token_obj.access_token = new_access_token
    token_obj.refresh_token = new_refresh_token
    token_obj.access_token_expires_at = access_token_expires_at.isoformat()
    token_obj.refresh_token_expires_at = refresh_token_expires_at.isoformat()
    
    db.commit()
    
    # Return new access token and new refresh token
    return new_access_token, new_refresh_token, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
