"""
API endpoints for token management (revocation, introspection).
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status, Body
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.db.session import get_db
from app.utils.auth import require_authenticated_user
from app.models.user import User
from app.middleware.oauth import revoke_token
from app.utils.logger import logger

router = APIRouter()

@router.post("/revoke", status_code=status.HTTP_200_OK)
async def revoke_token_endpoint(
    request: Request,
    token: Optional[str] = Body(None),
    reason: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user)
):
    """
    Revoke an OAuth token.
    
    If no token is provided, the current token used for authentication will be revoked.
    
    Args:
        request: Request object
        token: Token to revoke (optional)
        reason: Reason for revocation (optional)
        db: Database session
        current_user: Currently authenticated user
        
    Returns:
        Success message
    """
    # If no token is provided, use the current token
    if not token:
        token = getattr(request.state, "token", None)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No token provided and no current token found"
            )
    
    # Revoke the token
    success = revoke_token(db, token, reason)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to revoke token"
        )
    
    return {"message": "Token revoked successfully"}

@router.post("/introspect", status_code=status.HTTP_200_OK)
async def introspect_token(
    request: Request,
    token: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user)
):
    """
    Introspect an OAuth token to get information about it.
    
    Args:
        request: Request object
        token: Token to introspect
        db: Database session
        current_user: Currently authenticated user
        
    Returns:
        Token information
    """
    from app.utils.oauth import validate_access_token
    from app.models.token_blacklist import TokenBlacklist
    
    # Validate token
    token_obj = validate_access_token(db, token)
    
    if not token_obj:
        return {"active": False}
    
    # Check if token is blacklisted
    token_jti = token  # In a real implementation, you'd extract a JTI from the token
    is_blacklisted = await TokenBlacklist.is_blacklisted(db, token_jti)
    
    if is_blacklisted:
        return {"active": False}
    
    # Return token information
    return {
        "active": True,
        "scope": token_obj.scope,
        "client_id": str(token_obj.client.client_id),
        "user_id": str(token_obj.user_id),
        "exp": token_obj.access_token_expires_at
    }
