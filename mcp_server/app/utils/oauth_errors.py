"""
OAuth error handling utilities.
"""
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Optional, Dict, Any
from app.utils.logger import logger

class OAuthErrorResponse:
    """OAuth error response helper class."""
    
    @staticmethod
    def json_error(error: str, description: Optional[str] = None, status_code: int = 400) -> JSONResponse:
        """
        Create a JSON error response according to OAuth 2.0 spec.
        
        Args:
            error: Error code
            description: Error description
            status_code: HTTP status code
            
        Returns:
            JSONResponse with OAuth error format
        """
        content: Dict[str, Any] = {"error": error}
        if description:
            content["error_description"] = description
            
        logger.error(f"OAuth error: {error} - {description}")
        
        return JSONResponse(
            status_code=status_code,
            content=content
        )
    
    @staticmethod
    def redirect_error(
        redirect_uri: str,
        error: str,
        description: Optional[str] = None,
        state: Optional[str] = None
    ) -> RedirectResponse:
        """
        Create a redirect error response according to OAuth 2.0 spec.
        
        Args:
            redirect_uri: Client redirect URI
            error: Error code
            description: Error description
            state: State parameter from request
            
        Returns:
            RedirectResponse with OAuth error parameters
        """
        # Start with required error parameter
        query_params = f"error={error}"
        
        # Add optional parameters if provided
        if description:
            query_params += f"&error_description={description}"
        if state:
            query_params += f"&state={state}"
            
        # Log the error
        logger.error(f"OAuth redirect error: {error} - {description}")
        
        # Create the redirect URL with query parameters
        redirect_url = f"{redirect_uri}?{query_params}"
        
        return RedirectResponse(
            url=redirect_url,
            status_code=status.HTTP_302_FOUND
        )

# Standard OAuth error codes
class OAuthErrorCodes:
    """Standard OAuth 2.0 error codes."""
    INVALID_REQUEST = "invalid_request"
    INVALID_CLIENT = "invalid_client"
    INVALID_GRANT = "invalid_grant"
    UNAUTHORIZED_CLIENT = "unauthorized_client"
    UNSUPPORTED_GRANT_TYPE = "unsupported_grant_type"
    INVALID_SCOPE = "invalid_scope"
    ACCESS_DENIED = "access_denied"
    SERVER_ERROR = "server_error"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"
