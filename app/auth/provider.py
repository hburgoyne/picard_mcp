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
        print(f"=== Looking up client: {client_id} ===")
        async for db in get_db():
            # Find the client
            client_result = await db.execute(
                select(OAuthClient).where(OAuthClient.client_id == client_id)
            )
            client = client_result.scalars().first()
            
            if not client:
                print(f"Client not found: {client_id}")
                return None
            
            print(f"Found client: {client.client_id}")
            print(f"Client redirect URIs: {client.redirect_uris}")
            print(f"Client allowed scopes: {client.allowed_scopes}")
            
            # Convert the list of scopes to a space-separated string
            scope_str = ' '.join(client.allowed_scopes) if client.allowed_scopes else None
            print(f"Converted scope string: {scope_str}")
            
            return OAuthClientInformationFull(
                client_id=client.client_id,
                client_secret=client.client_secret,
                redirect_uris=[str(uri) for uri in client.redirect_uris],
                scope=scope_str  # Use scope (string) instead of scopes (list)
            )
    
    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        """Saves client information as part of registering it"""
        print(f"=== Registering client: {client_info.client_id} ===")
        print(f"Client scope: {client_info.scope}")
        
        # Extract scopes from the scope string
        client_scopes = client_info.scope.split() if client_info.scope else []
        print(f"Parsed scopes: {client_scopes}")
        
        async for db in get_db():
            # Check if client already exists
            client_result = await db.execute(
                select(OAuthClient).where(OAuthClient.client_id == client_info.client_id)
            )
            existing_client = client_result.scalars().first()
            
            if existing_client:
                # Update existing client
                existing_client.client_secret = client_info.client_secret
                existing_client.redirect_uris = [str(uri) for uri in client_info.redirect_uris]
                existing_client.allowed_scopes = client_scopes
                existing_client.updated_at = datetime.utcnow()
                print(f"Updated existing client with scopes: {client_scopes}")
            else:
                # Create new client
                client = OAuthClient(
                    client_id=client_info.client_id,
                    client_secret=client_info.client_secret,
                    redirect_uris=[str(uri) for uri in client_info.redirect_uris],
                    allowed_scopes=client_scopes
                )
                db.add(client)
                print(f"Created new client with scopes: {client_scopes}")
            
            await db.commit()
    
    async def authorize(self, client: OAuthClientInformationFull, params: AuthorizationParams) -> str:
        """Handle authorization request"""
        print("=== Authorization Request Received ===")
        print(f"Client ID: {client.client_id}")
        print(f"Redirect URI: {params.redirect_uri}")
        print(f"Requested Scopes: {params.scopes}")
        print(f"Requested Scopes Type: {type(params.scopes)}")
        print(f"State: {params.state}")
        print(f"Client object type: {type(client)}")
        print(f"Client dir: {dir(client)}")
        
        # Debug all client attributes
        print("=== Client Attributes ===")
        for attr in dir(client):
            if not attr.startswith('_'):
                try:
                    value = getattr(client, attr)
                    print(f"Client.{attr} = {value} (type: {type(value)})")
                except Exception as e:
                    print(f"Error accessing Client.{attr}: {e}")
        
        # Validate redirect URI
        if not params.redirect_uri:
            raise AuthorizeError(
                error="invalid_request",
                error_description="Missing redirect_uri"
            )
        
        # Validate scopes
        if params.scopes:
            print("=== Scope Validation Debug ===")
            # Convert the list of scopes to a set for comparison
            requested_scopes = set(params.scopes)
            print(f"Requested scopes: {requested_scopes}")
            
            # Try to get scopes from different possible attributes
            client_scopes = []
            if hasattr(client, 'scope') and client.scope is not None:
                print(f"Found client.scope: {client.scope} (type: {type(client.scope)})")
                # Split the scope string into a list
                client_scopes = client.scope.split()
            elif hasattr(client, 'scopes'):
                client_scopes = client.scopes
                print(f"Found client.scopes: {client_scopes} (type: {type(client_scopes)})")
            elif hasattr(client, 'allowed_scopes'):
                client_scopes = client.allowed_scopes
                print(f"Found client.allowed_scopes: {client_scopes} (type: {type(client_scopes)})")
            else:
                print("No scope, scopes, or allowed_scopes attribute found on client")
            
            allowed_scopes = set(client_scopes)
            
            print(f"Final allowed_scopes: {allowed_scopes}")
            print(f"Requested scopes: {requested_scopes}")
            
            # Check if all requested scopes are allowed
            invalid_scopes = requested_scopes - allowed_scopes
            if invalid_scopes:
                print(f"Invalid scopes detected: {invalid_scopes}")
                print(f"Requested: {requested_scopes}")
                print(f"Allowed: {allowed_scopes}")
                print(f"Difference: {requested_scopes - allowed_scopes}")
                raise AuthorizeError(
                    error="invalid_scope",
                    error_description=f"Client was not registered with scope {', '.join(invalid_scopes)}"
                )
            print("All requested scopes are valid.")
        
        print(f"params.redirect_uri = {params.redirect_uri}")
        
        # In a real implementation, this would redirect to a login page
        # For MVP, we'll auto-authorize the first user
        try:
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
                
                # Generate authorization code with proper integer timestamp for exp
                payload = {
                    "sub": str(user.id),
                    "client_id": client.client_id,
                    "scopes": params.scopes,
                    "redirect_uri": str(params.redirect_uri),
                    "code_challenge": params.code_challenge,
                    "code_challenge_method": params.code_challenge_method,
                    "exp": int((datetime.utcnow() + timedelta(minutes=10)).timestamp())
                }
                auth_code = jwt.encode(
                    payload,
                    settings.JWT_SECRET_KEY,
                    algorithm=settings.JWT_ALGORITHM
                )
                
                # Store the authorization code in the database
                auth_code_record = OAuthToken(
                    access_token=auth_code,  # Store as access_token since we don't have a separate auth code table
                    token_type="authorization_code",
                    scopes=params.scopes,
                    expires_at=datetime.fromtimestamp(payload["exp"]),
                    user_id=user.id,
                    client_id=client.client_id,
                    code_challenge=params.code_challenge,
                    code_challenge_method=params.code_challenge_method
                )
                db.add(auth_code_record)
                await db.commit()
                
                # Return redirect URI with code
                redirect_params = {"code": auth_code}
                if params.state:
                    redirect_params["state"] = params.state
                    
                from mcp.server.auth.provider import construct_redirect_uri
                try:
                    redirect_uri = construct_redirect_uri(str(params.redirect_uri), **redirect_params)
                    print("Redirecting to:", redirect_uri)
                    return redirect_uri
                except Exception as e:
                    print("Error constructing redirect URI:", e)
                    raise AuthorizeError(
                        error="server_error",
                        error_description="Failed to construct redirect URI"
                    )
        except Exception as e:
            print(f"Error in authorize: {e}")
            import traceback
            traceback.print_exc()
            raise AuthorizeError(
                error="server_error",
                error_description=f"Server error: {str(e)}"
            )
    
    async def load_authorization_code(self, client: OAuthClientInformationFull, authorization_code: str) -> AuthorizationCode | None:
        """Loads an AuthorizationCode by its code"""
        try:
            # Retrieve the authorization code from the database
            async for db in get_db():
                auth_code_result = await db.execute(
                    select(OAuthToken).where(
                        OAuthToken.access_token == authorization_code,
                        OAuthToken.token_type == "authorization_code"
                    )
                )
                auth_code_record = auth_code_result.scalars().first()
                
                if not auth_code_record:
                    return None
                    
                # Verify client ID
                if auth_code_record.client_id != client.client_id:
                    return None
                    
                # Verify code challenge method
                if auth_code_record.code_challenge_method != "S256":
                    return None
                    
                return AuthorizationCode(
                    code=authorization_code,
                    scopes=auth_code_record.scopes,
                    expires_at=auth_code_record.expires_at.timestamp(),
                    client_id=client.client_id,
                    code_challenge=auth_code_record.code_challenge,
                redirect_uri=payload["redirect_uri"],
                redirect_uri_provided_explicitly=True
            )
        except jwt.JWTError:
            return None
    
    async def exchange_authorization_code(self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode) -> OAuthToken:
        """Exchanges an authorization code for an access token and refresh token"""
        async for db in get_db():
            print("=== Authorization Code Exchange ===")
            print(f"Client ID: {client.client_id}")
            print(f"Authorization Code: {authorization_code.code[:10]}...{authorization_code.code[-10:]}")
            
            # Find the user
            try:
                payload = jwt.decode(
                    authorization_code.code,
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM]
                )
                print(f"JWT Payload: {payload}")
                print(f"JWT client_id: {payload.get('client_id', 'not found')}")
                
                user_id = payload["sub"]
                # Convert user_id from string to integer to match the database column type
                user_id_int = int(user_id)
                print(f"Looking up user with ID: {user_id} (converted from string: {user_id_int})")
                
                # Find the user
                user_result = await db.execute(
                    select(User).where(User.id == user_id_int)
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
                    "exp": int(access_token_expires.timestamp())  # Ensure exp is an integer timestamp
                }
                print(f"Creating access token with client_id: {client.client_id}")
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
                    "exp": int(refresh_token_expires.timestamp())  # Ensure exp is an integer timestamp
                }
                refresh_token = jwt.encode(
                    refresh_token_payload,
                    settings.JWT_SECRET_KEY,
                    algorithm=settings.JWT_ALGORITHM
                )
                
                # Get the OAuthClient record by client_id
                client_result = await db.execute(
                    select(OAuthClient).where(OAuthClient.client_id == client.client_id)
                )
                oauth_client = client_result.scalars().first()
                
                if not oauth_client:
                    print(f"=== TokenError being raised ===")
                    print(f"Error type: unauthorized_client")
                    print(f"Error description: Client not found")
                    print(f"Client ID: {client.client_id}")
                    print(f"OAuthClient ID: {oauth_client.id if oauth_client else None}")
                    raise TokenError(
                        error="unauthorized_client",
                        error_description="Client not found"
                    )
                
                # Store tokens in database
                token = OAuthToken(
                    user_id=int(user.id),  # Ensure user_id is an integer
                    client_id=oauth_client.id,  # Use the database ID instead of the client_id string
                    access_token=access_token,
                    refresh_token=refresh_token,
                    scopes=authorization_code.scopes,
                    expires_at=access_token_expires
                )
                print(f"Access token created with client_id type: {type(token.client_id)}")
                db.add(token)
                await db.commit()
                
                # Create response object with the correct fields
                response = {
                    "access_token": access_token,
                    "refresh_token": token.refresh_token,
                    "token_type": "bearer",
                    "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                    "scope": " ".join(authorization_code.scopes)
                }
                print(f"=== Returning token response ===")
                print(f"Access token: {access_token[:10]}... (truncated)")
                print(f"Refresh token: {token.refresh_token[:10]}... (truncated)")
                print(f"Expires in: {settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
                print(f"Scopes: {response['scope']}")
                return response
            except jwt.JWTError as e:
                print(f"JWT Error in exchange_authorization_code: {str(e)}")
                print(f"=== TokenError being raised ===")
                print(f"Error type: invalid_grant")
                print(f"Error description: Invalid authorization code: {str(e)}")
                print(f"Client ID: {client.client_id}")
                print(f"Authorization code: {authorization_code.code if hasattr(authorization_code, 'code') else None}")
                raise TokenError(
                    error="invalid_grant",
                    error_description=f"Invalid authorization code: {str(e)}"
                )
            except Exception as e:
                print(f"Unexpected error in exchange_authorization_code: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                raise TokenError(
                    error="server_error",
                    error_description=f"Server error: {str(e)}"
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
                "exp": int(access_token_expires.timestamp())  # Ensure exp is an integer timestamp
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
            
            # Create response object with the correct fields
            response = {
                "access_token": access_token,
                "refresh_token": token.refresh_token,
                "token_type": "bearer",
                "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "scope": " ".join(scopes or token.scopes)
            }
            print(f"=== Returning refresh token response ===")
            print(f"Access token: {access_token[:10]}... (truncated)")
            print(f"Refresh token: {token.refresh_token[:10]}... (truncated)")
            print(f"Expires in: {settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
            print(f"Scopes: {response['scope']}")
            return TokenResponse(
                access_token=response["access_token"],
                refresh_token=response["refresh_token"],
                token_type=response["token_type"],
                expires_in=response["expires_in"],
                scope=response["scope"]
            )
    
    async def token(self, request: TokenRequest) -> TokenResponse:
        """Handle token request"""
        print("=== Token Request Received ===")
        print(f"Grant type: {request.grant_type}")
        print(f"Client ID: {request.client_id}")
        print(f"Redirect URI: {request.redirect_uri}")
        print(f"Code: {request.code}")
        print(f"Refresh token: {request.refresh_token}")
        print(f"Requested scope: {request.scope}")
        
        try:
            if request.grant_type == "authorization_code":
                # Load authorization code
                # Get client information first
                client_info = await self.get_client(request.client_id)
                if not client_info:
                    return TokenResponse(
                        error="invalid_client",
                        error_description="Client not found"
                    )
                
                # Verify client secret
                if client_info.client_secret != request.client_secret:
                    return TokenResponse(
                        error="invalid_client",
                        error_description="Invalid client credentials"
                    )
                
                # Verify redirect URI
                if request.redirect_uri not in client_info.redirect_uris:
                    return TokenResponse(
                        error="invalid_request",
                        error_description="Invalid redirect URI"
                    )
                
                # Load authorization code
                authorization_code = await self.load_authorization_code(
                    client=client_info,
                    authorization_code=request.code
                )
                
                if not authorization_code:
                    print("Invalid authorization code")
                    return TokenResponse(
                        error="invalid_grant",
                        error_description="Invalid authorization code"
                    )
                
                # Exchange authorization code for tokens
                try:
                    print("Exchanging authorization code for tokens...")
                    tokens = await self.exchange_authorization_code(
                        client=client_info,
                        authorization_code=authorization_code
                    )
                    print(f"Successfully exchanged code for tokens: {tokens}")
                    return tokens
                except TokenError as e:
                    print("=== TokenError caught in token handler ===")
                    print(f"Error type: {e.error}")
                    print(f"Error description: {e.error_description}")
                    print(f"Client ID: {request.client_id}")
                    print(f"Grant type: {request.grant_type}")
                    print(f"Code: {request.code}")
                    print(f"Redirect URI: {request.redirect_uri}")
                    print(f"Scope: {request.scope}")
                    print(f"Full error object: {str(e)}")
                    
                    try:
                        # Attempt to create TokenErrorResponse directly
                        error_response = TokenResponse(
                            error=e.error,
                            error_description=e.error_description
                        )
                        print(f"Successfully created TokenErrorResponse: {error_response}")
                        return error_response
                    except Exception as creation_error:
                        print("=== Error creating TokenErrorResponse ===")
                        print(f"Error type: {type(creation_error).__name__}")
                        print(f"Error message: {str(creation_error)}")
                        print(f"Attempted error: {e.error}")
                        print(f"Attempted error_description: {e.error_description}")
                        
                        # Fallback to a basic error response
                        return TokenResponse(
                            error="invalid_request",
                            error_description="Internal server error occurred while processing request"
                        )
            
            elif request.grant_type == "refresh_token":
                # Get client information first
                client_info = await self.get_client(request.client_id)
                if not client_info:
                    return TokenResponse(
                        error="invalid_client",
                        error_description="Client not found"
                    )
                
                # Verify client secret
                if client_info.client_secret != request.client_secret:
                    return TokenResponse(
                        error="invalid_client",
                        error_description="Invalid client credentials"
                    )
                
                # Load refresh token
                refresh_token = await self.load_refresh_token(
                    client=client_info,
                    refresh_token=request.refresh_token
                )
                
                if not refresh_token:
                    print("Invalid refresh token")
                    return TokenResponse(
                        error="invalid_grant",
                        error_description="Invalid refresh token"
                    )
                
                # Exchange refresh token for tokens
                try:
                    scopes = request.scope.split() if request.scope else None
                    print("Exchanging refresh token for tokens...")
                    tokens = await self.exchange_refresh_token(
                        client=client_info,
                        refresh_token=refresh_token,
                        scopes=scopes
                    )
                    print(f"Successfully exchanged refresh token for tokens: {tokens}")
                    return tokens
                except TokenError as e:
                    print("=== TokenError caught in token handler ===")
                    print(f"Error type: {e.error}")
                    print(f"Error description: {e.error_description}")
                    print(f"Client ID: {request.client_id}")
                    print(f"Grant type: {request.grant_type}")
                    print(f"Refresh token: {request.refresh_token[:10]}... (truncated)")
                    print(f"Scope: {request.scope}")
                    print(f"Full error object: {str(e)}")
                    
                    try:
                        # Attempt to create TokenErrorResponse directly
                        error_response = TokenResponse(
                            error=e.error,
                            error_description=e.error_description
                        )
                        print(f"Successfully created TokenErrorResponse: {error_response}")
                        return error_response
                    except Exception as creation_error:
                        print("=== Error creating TokenErrorResponse ===")
                        print(f"Error type: {type(creation_error).__name__}")
                        print(f"Error message: {str(creation_error)}")
                        print(f"Attempted error: {e.error}")
                        print(f"Attempted error_description: {e.error_description}")
                        
                        # Fallback to a basic error response
                        return TokenResponse(
                            error="invalid_request",
                            error_description="Internal server error occurred while processing request"
                        )
            
            else:
                print(f"Unsupported grant type: {request.grant_type}")
                return TokenResponse(
                    error="unsupported_grant_type",
                    error_description="Unsupported grant type"
                )
        except Exception as e:
            print(f"Error in token: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return TokenResponse(
                error="server_error",
                error_description=str(e)
            )
    
    async def load_access_token(self, token: str) -> AccessToken | None:
        """Loads an access token by its token"""
        try:
            print("=== Token Validation Flow ===")
            print(f"Attempting to validate token: {token[:10]}...{token[-10:]}")  # Only show partial token for security
            
            async for db in get_db():
                # Find the token in database
                print("Looking up token in database...")
                token_result = await db.execute(
                    select(OAuthToken).where(OAuthToken.access_token == token)
                )
                db_token = token_result.scalars().first()
                
                if not db_token:
                    print("Token not found in database")
                    return None
                
                print(f"Found token with client_id type: {type(db_token.client_id)}")
                print(f"Token client_id value: {db_token.client_id}")
                print(f"Token scopes: {db_token.scopes}")
                print(f"Token expires_at: {db_token.expires_at}")
                
                # Check if token is expired
                if db_token.expires_at < datetime.utcnow():
                    print("Token has expired")
                    return None
                    
                try:
                    print("Attempting to decode JWT token...")
                    # Verify the token
                    payload = jwt.decode(
                        token,
                        settings.JWT_SECRET_KEY,
                        algorithms=[settings.JWT_ALGORITHM]
                    )
                    print(f"JWT payload: {payload}")
                    print(f"Payload client_id type: {type(payload.get('client_id', 'not found'))}")
                    
                    # Explicitly convert client_id to string
                    client_id = str(db_token.client_id)
                    print(f"Converted client_id to string: {client_id}")
                    
                    return AccessToken(
                        token=token,
                        client_id=client_id,
                        scopes=db_token.scopes,
                        expires_at=int(db_token.expires_at.timestamp())
                    )
                except jwt.JWTError as e:
                    print(f"JWT decoding error: {str(e)}")
                    return None
                    
        except Exception as e:
            print(f"Unexpected error in load_access_token: {str(e)}")
            raise
    
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
