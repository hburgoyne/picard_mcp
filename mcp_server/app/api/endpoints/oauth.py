"""
OAuth 2.0 API endpoints for authorization and token management.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status, Form, Response
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
import secrets
import uuid

from app.schemas.oauth import (
    AuthorizationRequest,
    TokenRequest
)
from app.models.oauth import OAuthClient, AuthorizationCode, Token
from app.models.user import User
from app.db.session import get_db
from app.core.config import settings
from app.utils.logger import logger
from app.utils.oauth import (
    create_authorization_code,
    create_access_token,
    refresh_access_token,
    validate_client,
    validate_redirect_uri,
    validate_client_credentials,
    validate_authorization_code,
    OAuthError
)
from app.utils.auth import get_current_user, require_authenticated_user
from app.utils.scope_descriptions import get_scope_descriptions
from app.core.config import settings

# Import templates directly
from app.main import templates

router = APIRouter()

@router.post("/consent")
async def consent(
    request: Request,
    client_id: uuid.UUID = Form(...),
    redirect_uri: str = Form(...),
    scope: str = Form(...),
    state: str = Form(...),
    response_type: str = Form(...),
    decision: str = Form(...),
    code_challenge: Optional[str] = Form(None),
    code_challenge_method: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user)
):
    """
    OAuth 2.0 consent endpoint.
    
    This endpoint processes the user's consent decision and either creates an authorization code
    or redirects back to the client with an error.
    
    Args:
        request: Request object
        client_id: OAuth client ID
        redirect_uri: Redirect URI for callback
        scope: Requested scopes
        state: State parameter for CSRF protection
        response_type: OAuth response type (must be "code")
        decision: User's decision ("approve" or "deny")
        code_challenge: PKCE code challenge
        code_challenge_method: PKCE code challenge method
        db: Database session
        current_user: Currently authenticated user
        
    Returns:
        Redirect to client with authorization code or error
    """
    try:
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
        
        # Check user's decision
        if decision.lower() != "approve":
            # User denied the authorization request
            return RedirectResponse(
                f"{redirect_uri}?error=access_denied&error_description=The+user+denied+the+request&state={state}",
                status_code=status.HTTP_302_FOUND
            )
        
        # Create authorization code
        auth_code = create_authorization_code(
            db=db,
            client_id=client.client_id,  # Use client_id field, not the primary key id
            user_id=current_user.id,
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
        logger.error(f"Error in consent endpoint: {str(e)}")
        if redirect_uri and state:
            return RedirectResponse(
                f"{redirect_uri}?error=server_error&state={state}",
                status_code=status.HTTP_302_FOUND
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server error"
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
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    OAuth 2.0 authorization endpoint.
    
    This endpoint validates the request parameters and redirects the user to a consent page
    if they are authenticated. If not authenticated, it redirects to the login page.
    
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
        current_user: Currently authenticated user
        
    Returns:
        Redirect to consent page, login page, or error redirect to client
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
                
        # Validate PKCE parameters
        if code_challenge_method and code_challenge_method not in ["S256"]:
            return RedirectResponse(
                f"{redirect_uri}?error=invalid_request&error_description=Unsupported+code+challenge+method&state={state}",
                status_code=status.HTTP_302_FOUND
            )
            
        # PKCE is required for all clients
        if not code_challenge:
            return RedirectResponse(
                f"{redirect_uri}?error=invalid_request&error_description=Code+challenge+required&state={state}",
                status_code=status.HTTP_302_FOUND
            )
            
        # If code_challenge is provided but method is not, default to S256
        if code_challenge and not code_challenge_method:
            code_challenge_method = "S256"
        
        # Check if user is authenticated
        logger.info(f"Authorization request: User authenticated: {current_user is not None}")
        if not current_user:
            logger.info("User not authenticated, redirecting to login_required error")
            # TODO: Implement a proper login page and redirect back to authorization
            # For now, return an error
            return RedirectResponse(
                f"{redirect_uri}?error=login_required&state={state}",
                status_code=status.HTTP_302_FOUND
            )
        else:
            logger.info(f"User authenticated: {current_user.username if hasattr(current_user, 'username') else current_user.id}")
        
        # Render the consent page
        scopes_with_descriptions = get_scope_descriptions(scope)
        logger.info(f"Rendering consent page with scopes: {scopes_with_descriptions}")
        
        try:
            # Use the templates object directly
            return templates.TemplateResponse(
                "consent.html",
                {
                    "request": request,
                    "client_id": client_id,
                    "client_name": client.client_name,
                    "redirect_uri": redirect_uri,
                    "scope": scope,
                    "state": state,
                    "response_type": response_type,
                    "code_challenge": code_challenge,
                    "code_challenge_method": code_challenge_method,
                    "scopes_with_descriptions": scopes_with_descriptions,
                    "action_url": f"{request.url.scheme}://{request.url.netloc}{settings.API_V1_STR}/oauth/consent"
                }
            )
        except Exception as e:
            logger.error(f"Error rendering consent template: {str(e)}")
            return RedirectResponse(
                f"{redirect_uri}?error=server_error&error_description=Error+rendering+consent+page&state={state}",
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
                
            # PKCE is required for all clients
            if not code_verifier:
                raise OAuthError("invalid_request", "Code verifier required")
                
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
                client_id=client.client_id,  # Use client_id field, not the primary key id
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
            # Validate required parameters for refresh_token grant
            if not refresh_token:
                raise OAuthError("invalid_request", "Refresh token required")
                
            # Refresh the access token
            result = refresh_access_token(db, refresh_token)
            if not result:
                raise OAuthError("invalid_grant", "Invalid or expired refresh token")
                
            new_access_token, new_refresh_token, expires_in = result
            
            # Get token object to retrieve scope
            token_obj = db.query(Token).filter(Token.refresh_token == new_refresh_token).first()
            if not token_obj:
                raise OAuthError("server_error", "Token not found after refresh")
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": expires_in,
                "refresh_token": new_refresh_token,
                "scope": token_obj.scope
            }
        
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
