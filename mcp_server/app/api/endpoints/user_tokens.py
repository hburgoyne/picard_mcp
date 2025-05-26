"""
User context token endpoint for client applications.

This endpoint allows trusted clients to obtain tokens for their users without
requiring the user to directly authenticate with the MCP server.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import hashlib
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.user import User
from app.models.oauth import OAuthClient, Token
from app.utils.oauth import (
    validate_client_credentials,
    validate_client,
    create_access_token
)
from app.utils.logger import logger

router = APIRouter()

@router.post("/user-token")
async def user_context_token(
    client_id: uuid.UUID = Form(...),
    client_secret: str = Form(...),
    username: str = Form(...),
    email: Optional[str] = Form(None),
    create_if_not_exists: bool = Form(False),
    db: Session = Depends(get_db)
):
    """
    Issue tokens for a user in the context of the authenticated client.
    
    This endpoint is used by trusted clients to obtain tokens for their users without
    requiring the user to directly authenticate with the MCP server.
    
    If create_if_not_exists is True and the user doesn't exist, a new user will be created.
    
    Args:
        client_id: OAuth client ID
        client_secret: OAuth client secret
        username: Username of the user to get tokens for
        email: Email of the user (required when creating a new user)
        create_if_not_exists: Whether to create the user if they don't exist
        db: Database session
        
    Returns:
        Access token, refresh token, and expiration information
    """
    try:
        # Validate client credentials
        client = validate_client(db, client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid client ID"
            )
        
        if not validate_client_credentials(client, client_secret):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid client credentials"
            )
        
        # Check if client is allowed to use this endpoint (should be a trusted client)
        if not client.is_confidential:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only confidential clients can use this endpoint"
            )
        
        # Find user
        user = db.query(User).filter(User.username == username).first()
        
        # Create user if not exists and requested
        if not user and create_if_not_exists:
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is required when creating a new user"
                )
            
            # Create a simple hashed password (user won't log in directly)
            random_password = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()
            
            user = User(
                username=username,
                email=email,
                hashed_password=random_password,
                is_active=True,
                is_superuser=False
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"Created new user via client credentials: {username}")
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive"
            )
        
        # Create tokens for the user
        # Use all scopes allowed for the client
        scope = " ".join(client.scopes)
        
        access_token, refresh_token, expires_in = create_access_token(
            db=db,
            client_id=client.client_id,
            user_id=user.id,
            scope=scope
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "refresh_token": refresh_token,
            "scope": scope
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in user context token endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred processing the request"
        )
