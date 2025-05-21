from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List, Dict, Any
from pydantic import ValidationError
import logging

from app.db.session import get_db
from app.models.user import User
from app.models.oauth import OAuthToken
from app.core.config import settings
from app.utils.security import decode_token
from app.schemas.token import TokenData

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/oauth/token",
    scopes={
        "memories:read": "Read access to memories",
        "memories:write": "Write access to memories",
        "profile:read": "Read access to user profile",
    },
)

logger = logging.getLogger(__name__)

async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current user from the token.
    
    Args:
        security_scopes: The security scopes required for the endpoint
        token: The JWT token
        db: The database session
        
    Returns:
        User: The current user
        
    Raises:
        HTTPException: If the token is invalid or the user doesn't have the required scopes
    """
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{" ".join(security_scopes.scopes)}"'
    else:
        authenticate_value = "Bearer"
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    
    try:
        # Decode the token
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Check token scopes
        token_scopes = payload.get("scopes", [])
        
        # Validate that the token has the required scopes
        for scope in security_scopes.scopes:
            if scope not in token_scopes:
                logger.warning(f"Token missing required scope: {scope}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not enough permissions. Required scope: {scope}",
                    headers={"WWW-Authenticate": authenticate_value},
                )
        
        # Get the user from the database
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        
        if user is None:
            logger.warning(f"User not found: {user_id}")
            raise credentials_exception
            
        return user
        
    except (JWTError, ValidationError) as e:
        logger.error(f"Token validation error: {e}")
        raise credentials_exception

# Dependency for endpoints that require memory:read scope
async def get_current_user_with_memory_read(
    current_user: User = Security(get_current_user, scopes=["memories:read"])
) -> User:
    """
    Get the current user with memory:read scope.
    """
    return current_user

# Dependency for endpoints that require memory:write scope
async def get_current_user_with_memory_write(
    current_user: User = Security(get_current_user, scopes=["memories:write"])
) -> User:
    """
    Get the current user with memory:write scope.
    """
    return current_user
