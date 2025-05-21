from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from authlib.oauth2 import OAuth2Error
from typing import Optional, Dict, Any, List
import uuid
import secrets
import time
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.oauth import OAuthClient, OAuthToken
from app.models.user import User
from app.schemas.oauth import (
    ClientRegistrationRequest, 
    ClientRegistrationResponse,
    TokenResponse
)
from app.core.config import settings
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash
)

router = APIRouter()

@router.post("/register", response_model=ClientRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_client(
    request: ClientRegistrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new OAuth client
    """
    # Generate client ID and secret
    client_id = str(uuid.uuid4())
    client_secret = secrets.token_urlsafe(32)
    
    # Create new OAuth client
    new_client = OAuthClient(
        client_id=client_id,
        client_secret=get_password_hash(client_secret),
        client_name=request.client_name,
        redirect_uris=request.redirect_uris,
        grant_types=request.grant_types,
        response_types=request.response_types,
        scopes=request.scopes,
        client_uri=request.client_uri,
        logo_uri=request.logo_uri,
        tos_uri=request.tos_uri,
        policy_uri=request.policy_uri,
        jwks_uri=request.jwks_uri,
        software_id=request.software_id,
        software_version=request.software_version
    )
    
    db.add(new_client)
    await db.commit()
    await db.refresh(new_client)
    
    # Return client credentials
    return ClientRegistrationResponse(
        client_id=client_id,
        client_secret=client_secret,
        client_id_issued_at=int(time.time()),
        client_secret_expires_at=0  # Never expires
    )

@router.post("/token", response_model=TokenResponse)
async def token_endpoint(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    redirect_uri: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth 2.0 token endpoint
    """
    # Validate client credentials
    result = await db.execute(select(OAuthClient).filter(OAuthClient.client_id == client_id))
    client = result.scalars().first()
    
    if not client or not verify_password(client_secret, client.client_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials"
        )
    
    if grant_type == "authorization_code":
        if not code or not redirect_uri:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required parameters for authorization_code grant"
            )
        
        # Validate authorization code
        # TODO: Implement authorization code validation
        
        # For now, just create a token for a demo user
        result = await db.execute(select(User).filter(User.username == "demo"))
        user = result.scalars().first()
        
        if not user:
            # Create a demo user if it doesn't exist
            user = User(
                username="demo",
                email="demo@example.com",
                hashed_password=get_password_hash("demo")
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        # Create access and refresh tokens
        access_token = create_access_token(
            data={"sub": user.id, "scopes": client.scopes.split()}
        )
        refresh_token = create_refresh_token(
            data={"sub": user.id}
        )
        
        # Store tokens in the database
        token = OAuthToken(
            access_token=access_token,
            refresh_token=refresh_token,
            client_id=client.id,
            user_id=user.id,
            scopes=client.scopes,
            expires_at=datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        db.add(token)
        await db.commit()
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=refresh_token,
            scope=client.scopes
        )
        
    elif grant_type == "refresh_token":
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing refresh_token parameter"
            )
        
        # Validate refresh token
        # TODO: Implement refresh token validation
        
        # For now, just create a new token
        result = await db.execute(select(User).filter(User.username == "demo"))
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        access_token = create_access_token(
            data={"sub": user.id, "scopes": client.scopes.split()}
        )
        new_refresh_token = create_refresh_token(
            data={"sub": user.id}
        )
        
        # Update token in the database
        result = await db.execute(
            select(OAuthToken).filter(
                OAuthToken.refresh_token == refresh_token,
                OAuthToken.client_id == client.id
            )
        )
        token = result.scalars().first()
        
        if token:
            token.access_token = access_token
            token.refresh_token = new_refresh_token
            token.expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            await db.commit()
        else:
            # Create new token record
            new_token = OAuthToken(
                access_token=access_token,
                refresh_token=new_refresh_token,
                client_id=client.id,
                user_id=user.id,
                scopes=client.scopes,
                expires_at=datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            db.add(new_token)
            await db.commit()
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=new_refresh_token,
            scope=client.scopes
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported grant_type: {grant_type}"
        )

@router.get("/authorize")
async def authorize(
    response_type: str,
    client_id: str,
    redirect_uri: str,
    scope: Optional[str] = None,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth 2.0 authorization endpoint
    """
    # Validate client
    result = await db.execute(select(OAuthClient).filter(OAuthClient.client_id == client_id))
    client = result.scalars().first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client_id"
        )
    
    # Validate redirect URI
    if redirect_uri not in client.redirect_uris.split():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect_uri"
        )
    
    # For now, automatically approve the authorization request
    # In a real implementation, this would show a consent screen
    
    # Generate authorization code
    auth_code = secrets.token_urlsafe(32)
    
    # Store the authorization code (would be implemented in a real system)
    # For now, we'll just redirect with the code
    
    # Build redirect URL
    redirect_url = f"{redirect_uri}?code={auth_code}"
    if state:
        redirect_url += f"&state={state}"
    
    return RedirectResponse(url=redirect_url)

@router.get("/userinfo")
async def userinfo(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth 2.0 userinfo endpoint
    """
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = auth_header.split(" ")[1]
    
    # Validate token
    result = await db.execute(select(OAuthToken).filter(OAuthToken.access_token == token))
    token_obj = result.scalars().first()
    
    if not token_obj or token_obj.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Get user info
    result = await db.execute(select(User).filter(User.id == token_obj.user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "sub": str(user.id),
        "username": user.username,
        "email": user.email
    }
