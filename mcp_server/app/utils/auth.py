"""
Authentication utility functions.
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.db.session import get_db
from app.models.user import User
from app.models.oauth import Token
from app.utils.oauth import validate_access_token
from app.utils.logger import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current authenticated user from the request.
    
    This function attempts to extract and validate an OAuth token from:
    1. The Authorization header (Bearer token)
    2. The session cookie
    3. The query parameters
    
    Args:
        request: FastAPI request object
        token: OAuth token from Authorization header
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
    """
    # Check Authorization header first (via oauth2_scheme)
    if token:
        token_obj = validate_access_token(db, token)
        if token_obj:
            user = db.query(User).filter(User.id == token_obj.user_id).first()
            if user and user.is_active:
                return user
    
    # Check for session cookie
    session_token = request.cookies.get("session_token")
    if session_token:
        token_obj = validate_access_token(db, session_token)
        if token_obj:
            user = db.query(User).filter(User.id == token_obj.user_id).first()
            if user and user.is_active:
                return user
    
    # Check query parameters (for OAuth flow)
    user_id_param = request.query_params.get("user_id")
    if user_id_param:
        try:
            user_id = uuid.UUID(user_id_param)
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.is_active:
                return user
        except (ValueError, TypeError):
            pass
    
    return None

def require_authenticated_user(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    Require an authenticated user for a route.
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        User if authenticated
        
    Raises:
        HTTPException: If user is not authenticated
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user
