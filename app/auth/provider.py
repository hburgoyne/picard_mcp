import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

from mcp.server.auth.provider import OAuthServerProvider
from mcp.server.auth.types import (
    AuthorizationRequest, AuthorizationResponse, TokenRequest, TokenResponse,
    TokenIntrospectionRequest, TokenIntrospectionResponse, RevocationRequest,
    ClientRegistrationRequest, ClientRegistrationResponse
)

from app.config import settings
from app.database import get_db
from app.models.oauth import OAuthClient, OAuthToken
from app.models.user import User

class PicardOAuthProvider(OAuthServerProvider):
    """OAuth provider for Picard MCP server"""
    
    async def authorize(self, request: AuthorizationRequest) -> AuthorizationResponse:
        """Handle authorization request"""
        # In a real implementation, this would redirect to a login page
        # For MVP, we'll auto-authorize the first user
        async for db in get_db():
            # Find the client
            client_result = await db.execute(
                select(OAuthClient).where(OAuthClient.client_id == request.client_id)
            )
            client = client_result.scalars().first()
            
            if not client:
                return AuthorizationResponse(
                    error="invalid_client",
                    error_description="Client not found"
                )
            
            # Find or create a user (for MVP)
            user_result = await db.execute(select(User).limit(1))
            user = user_result.scalars().first()
            
            if not user:
                # Create a default user for testing
                user = User(
                    username="test_user",
                    email="test@example.com",
                    hashed_password="hashed_password"  # In production, use proper hashing
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
            
            # Generate authorization code
            auth_code = jwt.encode(
                {
                    "sub": str(user.id),
                    "client_id": client.client_id,
                    "scopes": request.scope.split(),
                    "redirect_uri": request.redirect_uri,
                    "exp": datetime.utcnow() + timedelta(minutes=10)
                },
                settings.JWT_SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM
            )
            
            # Return successful response
            return AuthorizationResponse(
                code=auth_code,
                state=request.state
            )
    
    async def token(self, request: TokenRequest) -> TokenResponse:
        """Handle token request"""
        async for db in get_db():
            if request.grant_type == "authorization_code":
                # Validate authorization code
                try:
                    payload = jwt.decode(
                        request.code,
                        settings.JWT_SECRET_KEY,
                        algorithms=[settings.JWT_ALGORITHM]
                    )
                    
                    # Verify client ID
                    if payload["client_id"] != request.client_id:
                        return TokenResponse(
                            error="invalid_grant",
                            error_description="Client ID mismatch"
                        )
                    
                    # Verify redirect URI
                    if payload["redirect_uri"] != request.redirect_uri:
                        return TokenResponse(
                            error="invalid_grant",
                            error_description="Redirect URI mismatch"
                        )
                    
                    # Find the client
                    client_result = await db.execute(
                        select(OAuthClient).where(OAuthClient.client_id == request.client_id)
                    )
                    client = client_result.scalars().first()
                    
                    if not client:
                        return TokenResponse(
                            error="invalid_client",
                            error_description="Client not found"
                        )
                    
                    # Find the user
                    user_id = int(payload["sub"])
                    user_result = await db.execute(
                        select(User).where(User.id == user_id)
                    )
                    user = user_result.scalars().first()
                    
                    if not user:
                        return TokenResponse(
                            error="invalid_grant",
                            error_description="User not found"
                        )
                    
                    # Generate access token
                    access_token = jwt.encode(
                        {
                            "sub": str(user.id),
                            "client_id": client.client_id,
                            "scopes": payload["scopes"],
                            "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
                        },
                        settings.JWT_SECRET_KEY,
                        algorithm=settings.JWT_ALGORITHM
                    )
                    
                    # Generate refresh token
                    refresh_token = jwt.encode(
                        {
                            "sub": str(user.id),
                            "client_id": client.client_id,
                            "scopes": payload["scopes"],
                            "exp": datetime.utcnow() + timedelta(days=30)
                        },
                        settings.JWT_SECRET_KEY,
                        algorithm=settings.JWT_ALGORITHM
                    )
                    
                    # Calculate expiration
                    expires_at = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
                    
                    # Store token in database
                    token = OAuthToken(
                        access_token=access_token,
                        refresh_token=refresh_token,
                        token_type="bearer",
                        scopes=payload["scopes"],
                        expires_at=expires_at,
                        user_id=user.id,
                        client_id=client.id
                    )
                    db.add(token)
                    await db.commit()
                    
                    # Return successful response
                    return TokenResponse(
                        access_token=access_token,
                        token_type="bearer",
                        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                        refresh_token=refresh_token,
                        scope=" ".join(payload["scopes"])
                    )
                    
                except jwt.JWTError:
                    return TokenResponse(
                        error="invalid_grant",
                        error_description="Invalid authorization code"
                    )
            
            elif request.grant_type == "refresh_token":
                # Validate refresh token
                try:
                    payload = jwt.decode(
                        request.refresh_token,
                        settings.JWT_SECRET_KEY,
                        algorithms=[settings.JWT_ALGORITHM]
                    )
                    
                    # Verify client ID
                    if payload["client_id"] != request.client_id:
                        return TokenResponse(
                            error="invalid_grant",
                            error_description="Client ID mismatch"
                        )
                    
                    # Find the client
                    client_result = await db.execute(
                        select(OAuthClient).where(OAuthClient.client_id == request.client_id)
                    )
                    client = client_result.scalars().first()
                    
                    if not client:
                        return TokenResponse(
                            error="invalid_client",
                            error_description="Client not found"
                        )
                    
                    # Find the user
                    user_id = int(payload["sub"])
                    user_result = await db.execute(
                        select(User).where(User.id == user_id)
                    )
                    user = user_result.scalars().first()
                    
                    if not user:
                        return TokenResponse(
                            error="invalid_grant",
                            error_description="User not found"
                        )
                    
                    # Generate new access token
                    access_token = jwt.encode(
                        {
                            "sub": str(user.id),
                            "client_id": client.client_id,
                            "scopes": payload["scopes"],
                            "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
                        },
                        settings.JWT_SECRET_KEY,
                        algorithm=settings.JWT_ALGORITHM
                    )
                    
                    # Calculate expiration
                    expires_at = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
                    
                    # Update token in database
                    token_result = await db.execute(
                        select(OAuthToken).where(OAuthToken.refresh_token == request.refresh_token)
                    )
                    token = token_result.scalars().first()
                    
                    if token:
                        token.access_token = access_token
                        token.expires_at = expires_at
                        await db.commit()
                    else:
                        # Create new token
                        token = OAuthToken(
                            access_token=access_token,
                            refresh_token=request.refresh_token,
                            token_type="bearer",
                            scopes=payload["scopes"],
                            expires_at=expires_at,
                            user_id=user.id,
                            client_id=client.id
                        )
                        db.add(token)
                        await db.commit()
                    
                    # Return successful response
                    return TokenResponse(
                        access_token=access_token,
                        token_type="bearer",
                        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                        scope=" ".join(payload["scopes"])
                    )
                    
                except jwt.JWTError:
                    return TokenResponse(
                        error="invalid_grant",
                        error_description="Invalid refresh token"
                    )
            
            else:
                return TokenResponse(
                    error="unsupported_grant_type",
                    error_description="Unsupported grant type"
                )
    
    async def introspect(self, request: TokenIntrospectionRequest) -> TokenIntrospectionResponse:
        """Handle token introspection request"""
        async for db in get_db():
            # Find the token in database
            token_result = await db.execute(
                select(OAuthToken).where(OAuthToken.access_token == request.token)
            )
            token = token_result.scalars().first()
            
            if not token:
                return TokenIntrospectionResponse(active=False)
            
            # Check if token is expired
            if token.expires_at < datetime.utcnow():
                return TokenIntrospectionResponse(active=False)
            
            # Return token information
            return TokenIntrospectionResponse(
                active=True,
                scope=" ".join(token.scopes),
                client_id=token.client.client_id,
                username=token.user.username,
                exp=int(token.expires_at.timestamp()),
                sub=str(token.user_id),
                iss=settings.MCP_ISSUER_URL
            )
    
    async def revoke(self, request: RevocationRequest) -> None:
        """Handle token revocation request"""
        async for db in get_db():
            # Find the token in database
            token_result = await db.execute(
                select(OAuthToken).where(
                    (OAuthToken.access_token == request.token) | 
                    (OAuthToken.refresh_token == request.token)
                )
            )
            token = token_result.scalars().first()
            
            if token:
                # Delete the token
                await db.delete(token)
                await db.commit()
    
    async def register_client(self, request: ClientRegistrationRequest) -> ClientRegistrationResponse:
        """Handle client registration request"""
        async for db in get_db():
            # Check if client already exists
            client_result = await db.execute(
                select(OAuthClient).where(OAuthClient.client_id == request.client_id)
            )
            client = client_result.scalars().first()
            
            if client:
                return ClientRegistrationResponse(
                    error="invalid_client_metadata",
                    error_description="Client already exists"
                )
            
            # Create new client
            client = OAuthClient(
                client_id=request.client_id,
                client_secret=request.client_secret,
                redirect_uris=request.redirect_uris,
                allowed_scopes=request.scope.split()
            )
            db.add(client)
            await db.commit()
            await db.refresh(client)
            
            # Return client information
            return ClientRegistrationResponse(
                client_id=client.client_id,
                client_secret=client.client_secret,
                client_id_issued_at=int(client.created_at.timestamp()),
                client_secret_expires_at=0,  # Never expires
                redirect_uris=client.redirect_uris,
                grant_types=["authorization_code", "refresh_token"],
                token_endpoint_auth_method="client_secret_basic",
                scope=" ".join(client.allowed_scopes)
            )
