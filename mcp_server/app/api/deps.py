"""
OAuth security dependencies for FastAPI.
"""
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2AuthorizationCodeBearer, SecurityScopes
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import ValidationError

from app.db.session import get_db
from app.models.oauth import Token
from app.models.user import User
from app.utils.oauth import validate_access_token
from app.utils.logger import logger

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"/api/oauth/token",
    scopes={
        "memories:read": "Read access to memories",
        "memories:write": "Write access to memories",
        "memories:admin": "Administrative access to memories"
    }
)

def get_current_token(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[Token]:
    """
    Get and validate the current access token.
    
    Args:
        security_scopes: Required scopes for the endpoint
        token: Access token from Authorization header
        db: Database session
        
    Returns:
        Token object if valid
        
    Raises:
        HTTPException: If token is invalid or missing required scopes
    """
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{" ".join(security_scopes.scopes)}"'
    else:
        authenticate_value = "Bearer"
        
    # Define the error response
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    
    try:
        # Validate the token
        token_obj = validate_access_token(db, token)
        if token_obj is None:
            raise credentials_exception
            
        # Check required scopes
        if security_scopes.scopes:
            token_scopes = token_obj.scope.split()
            for scope in security_scopes.scopes:
                if scope not in token_scopes:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not enough permissions",
                        headers={"WWW-Authenticate": authenticate_value},
                    )
                    
        return token_obj
        
    except ValidationError:
        logger.error("Token validation error")
        raise credentials_exception

def get_current_user(
    token: Token = Depends(get_current_token),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user.
    
    Args:
        token: Current valid token
        db: Database session
        
    Returns:
        User object if valid
        
    Raises:
        HTTPException: If user is not found
    """
    user = db.query(User).filter(User.id == token.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user
