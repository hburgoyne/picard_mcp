import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

# Import the OAuthAuthorizationServerProvider class
from mcp.server.auth.provider import OAuthAuthorizationServerProvider as OAuthServerProvider

# Import the shared auth types
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

# Import the dataclasses for authorization parameters
from mcp.server.auth.provider import (
    AuthorizationParams, AuthorizationCode, RefreshToken, AccessToken,
    TokenError, AuthorizeError, RegistrationError
)

# Define the request and response types for our implementation
from pydantic import BaseModel
from typing import Optional, List

class TokenRequest(BaseModel):
    grant_type: str
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    client_id: str
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    error: Optional[str] = None
    error_description: Optional[str] = None

class TokenIntrospectionRequest(BaseModel):
    token: str

class TokenIntrospectionResponse(BaseModel):
    active: bool
    scope: Optional[str] = None
    client_id: Optional[str] = None
    username: Optional[str] = None
    exp: Optional[int] = None
    sub: Optional[str] = None
    iss: Optional[str] = None

class RevocationRequest(BaseModel):
    token: str
    token_type_hint: Optional[str] = None

class ClientRegistrationRequest(BaseModel):
    client_id: str
    client_secret: str
    redirect_uris: List[str]
    scope: str

class ClientRegistrationResponse(BaseModel):
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    client_id_issued_at: Optional[int] = None
    client_secret_expires_at: Optional[int] = None
    redirect_uris: Optional[List[str]] = None
    grant_types: Optional[List[str]] = None
    token_endpoint_auth_method: Optional[str] = None
    scope: Optional[str] = None
    error: Optional[str] = None
    error_description: Optional[str] = None

from app.config import settings
from app.database import get_db
from app.models.oauth import OAuthClient, OAuthToken
from app.models.user import User

class PicardOAuthProvider(OAuthServerProvider):
    """OAuth provider for Picard MCP server"""
    
    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        """Retrieves client information by client ID"""
        async for db in get_db():
            # Find the client
            client_result = await db.execute(
                select(OAuthClient).where(OAuthClient.client_id == client_id)
            )
            client = client_result.scalars().first()
            
            if not client:
                return None
            
            return OAuthClientInformationFull(
                client_id=client.client_id,
                client_secret=client.client_secret,
                redirect_uris=[uri for uri in client.redirect_uris],
                scopes=client.allowed_scopes
            )
    
    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        """Saves client information as part of registering it"""
        async for db in get_db():
            # Check if client already exists
            client_result = await db.execute(
                select(OAuthClient).where(OAuthClient.client_id == client_info.client_id)
            )
            client = client_result.scalars().first()
            
            if client:
                raise RegistrationError(
                    error="invalid_client_metadata",
                    error_description="Client already exists"
                )
            
            # Create new client
            client = OAuthClient(
                client_id=client_info.client_id,
                client_secret=client_info.client_secret,
                redirect_uris=client_info.redirect_uris,
                allowed_scopes=client_info.scopes
            )
            db.add(client)
            await db.commit()
    
    async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams) -> str:
        """Handle authorization request"""
        # In a real implementation, this would redirect to a login page
        # For MVP, we'll auto-authorize the first user
        async for db in get_db():
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
                    "scopes": params.scopes,
                    "redirect_uri": str(params.redirect_uri),
                    "code_challenge": params.code_challenge,
                    "exp": datetime.utcnow() + timedelta(minutes=10)
                },
                settings.JWT_SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM
            )
            
            # Store the authorization code
            # In a real implementation, you would store this in the database
            
            # Return redirect URI with code
            redirect_params = {"code": auth_code}
            if params.state:
                redirect_params["state"] = params.state
                
            from mcp.server.auth.provider import construct_redirect_uri
            return construct_redirect_uri(str(params.redirect_uri), **redirect_params)
    
    async def load_authorization_code(self, client: OAuthClientInformationFull, authorization_code: str) -> AuthorizationCode | None:
        """Loads an AuthorizationCode by its code"""
        try:
            # In a real implementation, you would retrieve this from the database
            # For MVP, we'll decode the JWT
            payload = jwt.decode(
                authorization_code,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Verify client ID
            if payload["client_id"] != client.client_id:
                return None
            
            return AuthorizationCode(
                code=authorization_code,
                scopes=payload["scopes"],
                expires_at=payload["exp"],
                client_id=client.client_id,
                code_challenge=payload["code_challenge"],
                redirect_uri=payload["redirect_uri"],
                redirect_uri_provided_explicitly=True
            )
        except jwt.JWTError:
            return None
    
    async def exchange_authorization_code(self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode) -> OAuthToken:
        """Exchanges an authorization code for an access token and refresh token"""
        async for db in get_db():
            # Find the user
            try:
                payload = jwt.decode(
                    authorization_code.code,
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM]
                )
                user_id = payload["sub"]
                user_result = await db.execute(
                    select(User).where(User.id == user_id)
                )
                user = user_result.scalars().first()
                
                if not user:
                    raise TokenError(
                        error="invalid_grant",
                        error_description="User not found"
                    )
                
                # Generate access token
                access_token_expires = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token_payload = {
                    "sub": user_id,
                    "client_id": client.client_id,
                    "scopes": authorization_code.scopes,
                    "exp": int(access_token_expires.timestamp())
                }
                access_token = jwt.encode(
                    access_token_payload,
                    settings.JWT_SECRET_KEY,
                    algorithm=settings.JWT_ALGORITHM
                )
                
                # Generate refresh token
                refresh_token_expires = datetime.utcnow() + timedelta(days=30)
                refresh_token_payload = {
                    "sub": user_id,
                    "client_id": client.client_id,
                    "scopes": authorization_code.scopes,
                    "exp": int(refresh_token_expires.timestamp())
                }
                refresh_token = jwt.encode(
                    refresh_token_payload,
                    settings.JWT_SECRET_KEY,
                    algorithm=settings.JWT_ALGORITHM
                )
                
                # Store tokens in database
                token = OAuthToken(
                    user_id=user.id,
                    client_id=client.client_id,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    scopes=authorization_code.scopes,
                    expires_at=access_token_expires
                )
                db.add(token)
                await db.commit()
                
                # Return tokens
                return OAuthToken(
                    access_token=access_token,
                    token_type="bearer",
                    expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                    refresh_token=refresh_token,
                    scope=" ".join(authorization_code.scopes)
                )
            except jwt.JWTError:
                raise TokenError(
                    error="invalid_grant",
                    error_description="Invalid authorization code"
                )
    
    async def load_refresh_token(self, client: OAuthClientInformationFull, refresh_token: str) -> RefreshToken | None:
        """Loads a RefreshToken by its token string"""
        async for db in get_db():
            # Find the token in database
            token_result = await db.execute(
                select(OAuthToken).where(OAuthToken.refresh_token == refresh_token)
            )
            token = token_result.scalars().first()
            
            if not token or token.client_id != client.client_id:
                return None
            
            try:
                # Verify the token
                payload = jwt.decode(
                    refresh_token,
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM]
                )
                
                return RefreshToken(
                    token=refresh_token,
                    client_id=client.client_id,
                    scopes=token.scopes,
                    expires_at=payload.get("exp")
                )
            except jwt.JWTError:
                return None
    
    async def exchange_refresh_token(self, client: OAuthClientInformationFull, refresh_token: RefreshToken, scopes: list[str]) -> OAuthToken:
        """Exchanges a refresh token for an access token and refresh token"""
        async for db in get_db():
            # Find the token in database
            token_result = await db.execute(
                select(OAuthToken).where(OAuthToken.refresh_token == refresh_token.token)
            )
            token = token_result.scalars().first()
            
            if not token:
                raise TokenError(
                    error="invalid_grant",
                    error_description="Refresh token not found"
                )
            
            # Generate new access token
            access_token_expires = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token_payload = {
                "sub": str(token.user_id),
                "client_id": token.client_id,
                "scopes": scopes or token.scopes,
                "exp": int(access_token_expires.timestamp())
            }
            access_token = jwt.encode(
                access_token_payload,
                settings.JWT_SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM
            )
            
            # Update token in database
            token.access_token = access_token
            token.expires_at = access_token_expires
            await db.commit()
            
            # Return tokens
            return OAuthToken(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                refresh_token=token.refresh_token,
                scope=" ".join(scopes or token.scopes)
            )
    
    async def token(self, request: TokenRequest) -> TokenResponse:
        """Handle token request"""
        async for db in get_db():
            if request.grant_type == "authorization_code":
                # Load authorization code
                authorization_code = await self.load_authorization_code(
                    client=OAuthClientInformationFull(
                        client_id=request.client_id,
                        client_secret=request.client_secret,
                        redirect_uris=[request.redirect_uri],
                        scopes=[]
                    ),
                    authorization_code=request.code
                )
                
                if not authorization_code:
                    return TokenResponse(
                        error="invalid_grant",
                        error_description="Invalid authorization code"
                    )
                
                # Exchange authorization code for tokens
                try:
                    return await self.exchange_authorization_code(
                        client=OAuthClientInformationFull(
                            client_id=request.client_id,
                            client_secret=request.client_secret,
                            redirect_uris=[request.redirect_uri],
                            scopes=[]
                        ),
                        authorization_code=authorization_code
                    )
                except TokenError as e:
                    return TokenResponse(
                        error=e.error,
                        error_description=e.error_description
                    )
            
            elif request.grant_type == "refresh_token":
                # Load refresh token
                refresh_token = await self.load_refresh_token(
                    client=OAuthClientInformationFull(
                        client_id=request.client_id,
                        client_secret=request.client_secret,
                        redirect_uris=[request.redirect_uri],
                        scopes=[]
                    ),
                    refresh_token=request.refresh_token
                )
                
                if not refresh_token:
                    return TokenResponse(
                        error="invalid_grant",
                        error_description="Invalid refresh token"
                    )
                
                # Exchange refresh token for tokens
                try:
                    scopes = request.scope.split() if request.scope else None
                    return await self.exchange_refresh_token(
                        client=OAuthClientInformationFull(
                            client_id=request.client_id,
                            client_secret=request.client_secret,
                            redirect_uris=[request.redirect_uri],
                            scopes=[]
                        ),
                        refresh_token=refresh_token,
                        scopes=scopes
                    )
                except TokenError as e:
                    return TokenResponse(
                        error=e.error,
                        error_description=e.error_description
                    )
            
            else:
                return TokenResponse(
                    error="unsupported_grant_type",
                    error_description="Unsupported grant type"
                )
    
    async def load_access_token(self, token: str) -> AccessToken | None:
        """Loads an access token by its token"""
        async for db in get_db():
            # Find the token in database
            token_result = await db.execute(
                select(OAuthToken).where(OAuthToken.access_token == token)
            )
            db_token = token_result.scalars().first()
            
            if not db_token:
                return None
            
            # Check if token is expired
            if db_token.expires_at < datetime.utcnow():
                return None
            
            try:
                # Verify the token
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM]
                )
                
                return AccessToken(
                    token=token,
                    client_id=db_token.client_id,
                    scopes=db_token.scopes,
                    expires_at=int(db_token.expires_at.timestamp())
                )
            except jwt.JWTError:
                return None
    
    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        """Revokes an access or refresh token"""
        async for db in get_db():
            # Find the token in database
            token_result = await db.execute(
                select(OAuthToken).where(
                    (OAuthToken.access_token == token.token) | 
                    (OAuthToken.refresh_token == token.token)
                )
            )
            db_token = token_result.scalars().first()
            
            if db_token:
                # Delete the token
                await db.delete(db_token)
                await db.commit()
