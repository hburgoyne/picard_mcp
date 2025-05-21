"""
OAuth 2.0 API endpoints for authorization and token management.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import secrets
import uuid

from app.schemas.oauth import (
    OAuthClientCreate,
    OAuthClientRegisterResponse, 
    AuthorizationRequest,
    TokenRequest
)
from app.models.oauth import OAuthClient, AuthorizationCode, Token
from app.db.session import get_db
from app.core.config import settings
from app.utils.logger import logger
from app.utils.oauth import (
    create_authorization_code,
    create_access_token,
    validate_client,
    validate_redirect_uri,
    validate_client_credentials,
    validate_authorization_code,
    OAuthError
)

router = APIRouter()

@router.post("/register", response_model=OAuthClientRegisterResponse)
async def register_client(
    client_data: OAuthClientCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new OAuth client.
    
    Args:
        client_data: Client registration data
        db: Database session
        
    Returns:
        Registered client information with client credentials
    """
    try:
        # Generate client secret
        client_secret = secrets.token_urlsafe(32)
        
        # Create new OAuth client
        new_client = OAuthClient(
            client_id=uuid.uuid4(),
            client_secret=client_secret,
            client_name=client_data.client_name,
            redirect_uris=client_data.redirect_uris,
            scopes=client_data.scopes,
            is_confidential=client_data.is_confidential
        )
        
        db.add(new_client)
        db.commit()
        db.refresh(new_client)
        
        # Return client credentials
        return {
            "client_id": new_client.client_id,
            "client_secret": client_secret,
            "client_name": new_client.client_name,
            "redirect_uris": new_client.redirect_uris,
            "scopes": new_client.scopes,
            "is_confidential": new_client.is_confidential
        }
        
    except Exception as e:
        logger.error(f"Error registering client: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registering OAuth client"
        )

@router.get("/authorize")
async def authorize(
    request: Request,
    response_type: str,
    client_id: uuid.UUID,
    redirect_uri: str,
    scope: str,
    state: str,
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    OAuth 2.0 authorization endpoint.
    
    This endpoint should redirect the user to a consent page where they can approve or deny
    the authorization request. For now, it automatically creates an authorization code.
    
    Args:
        request: Request object
        response_type: OAuth response type (must be "code")
        client_id: OAuth client ID
        redirect_uri: Redirect URI for callback
        scope: Requested scopes
        state: State parameter for CSRF protection
        code_challenge: PKCE code challenge
        code_challenge_method: PKCE code challenge method
        db: Database session
        
    Returns:
        Redirect to client with authorization code or error
    """
    try:
        # Validate parameters
        if response_type != "code":
            return RedirectResponse(
                f"{redirect_uri}?error=unsupported_response_type&state={state}",
                status_code=status.HTTP_302_FOUND
            )
        
        # Validate client
        client = validate_client(db, client_id)
        if not client:
            return RedirectResponse(
                f"{redirect_uri}?error=invalid_client&state={state}",
                status_code=status.HTTP_302_FOUND
            )
        
        # Validate redirect URI
        if not validate_redirect_uri(client, redirect_uri):
            raise OAuthError("invalid_request", "Invalid redirect URI")
            
        # Validate scopes
        requested_scopes = scope.split()
        for req_scope in requested_scopes:
            if req_scope not in client.scopes:
                return RedirectResponse(
                    f"{redirect_uri}?error=invalid_scope&state={state}",
                    status_code=status.HTTP_302_FOUND
                )
        
        # TODO: Redirect to a consent page instead of auto-approving
        # For now, we'll auto-approve and create an authorization code
        
        # Create authorization code
        # In a real implementation, this would happen after user consent
        auth_code = create_authorization_code(
            db=db,
            client_id=client.id,
            user_id=uuid.UUID('00000000-0000-0000-0000-000000000000'),  # Placeholder - will be replaced with real user ID
            redirect_uri=redirect_uri,
            scope=scope,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method
        )
        
        # Redirect back to client with authorization code
        return RedirectResponse(
            f"{redirect_uri}?code={auth_code}&state={state}",
            status_code=status.HTTP_302_FOUND
        )
        
    except OAuthError as e:
        # Handle OAuth-specific errors
        if redirect_uri and state:
            return RedirectResponse(
                f"{redirect_uri}?error={e.error}&error_description={e.description}&state={state}",
                status_code=status.HTTP_302_FOUND
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{e.error}: {e.description}"
        )
    except Exception as e:
        logger.error(f"Error in authorization endpoint: {str(e)}")
        if redirect_uri and state:
            return RedirectResponse(
                f"{redirect_uri}?error=server_error&state={state}",
                status_code=status.HTTP_302_FOUND
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error"
        )

@router.post("/token")
async def token(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    client_id: uuid.UUID = Form(...),
    client_secret: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    OAuth 2.0 token endpoint.
    
    This endpoint handles token requests, including authorization code exchange
    and refresh token requests.
    
    Args:
        grant_type: OAuth grant type
        code: Authorization code (for authorization_code grant)
        redirect_uri: Redirect URI (for authorization_code grant)
        client_id: OAuth client ID
        client_secret: OAuth client secret
        code_verifier: PKCE code verifier (for authorization_code grant with PKCE)
        refresh_token: Refresh token (for refresh_token grant)
        db: Database session
        
    Returns:
        Access token response
    """
    try:
        # Validate client
        client = validate_client(db, client_id)
        if not client:
            raise OAuthError("invalid_client", "Invalid client")
            
        # Validate client credentials for confidential clients
        if client.is_confidential:
            if not client_secret:
                raise OAuthError("invalid_client", "Client authentication required")
            if not validate_client_credentials(client, client_secret):
                raise OAuthError("invalid_client", "Invalid client credentials")
        
        if grant_type == "authorization_code":
            # Validate required parameters for authorization_code grant
            if not code or not redirect_uri:
                raise OAuthError("invalid_request", "Missing required parameters")
                
            # Validate authorization code
            auth_code = validate_authorization_code(
                db=db,
                code=code,
                client_id=client.id,
                redirect_uri=redirect_uri,
                code_verifier=code_verifier
            )
            
            # Create tokens
            access_token, refresh_token, expires_in = create_access_token(
                db=db,
                client_id=client.id,
                user_id=auth_code.user_id,
                scope=auth_code.scope
            )
            
            # Delete used authorization code
            db.delete(auth_code)
            db.commit()
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": expires_in,
                "refresh_token": refresh_token,
                "scope": auth_code.scope
            }
            
        elif grant_type == "refresh_token":
            # TODO: Implement refresh token flow
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Refresh token flow not yet implemented"
            )
        
        else:
            raise OAuthError("unsupported_grant_type", "Unsupported grant type")
            
    except OAuthError as e:
        # Handle OAuth-specific errors
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": e.error,
                "error_description": e.description
            }
        )
    except Exception as e:
        logger.error(f"Error in token endpoint: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "server_error",
                "error_description": "An error occurred processing the token request"
            }
        )
