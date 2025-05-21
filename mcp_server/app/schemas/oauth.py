from pydantic import BaseModel, UUID4, Field, field_validator, HttpUrl, validator, ConfigDict
from typing import Optional, List, Union
from datetime import datetime
import uuid

def validate_scopes(scopes: List[str]) -> List[str]:
    """Validate scope values."""
    valid_scopes = ["memories:read", "memories:write", "profile:read", "profile:write"]
    for scope in scopes:
        if scope not in valid_scopes:
            raise ValueError(f"Invalid scope: {scope}. Valid scopes are: {', '.join(valid_scopes)}")
    return scopes

class OAuthClientBase(BaseModel):
    """Base schema for OAuth client data."""
    client_name: str
    redirect_uris: List[str]
    scopes: List[str]
    is_confidential: bool = True

    @field_validator("scopes")
    def validate_scopes(cls, v):
        """Validate scope values."""
        return validate_scopes(v)

class OAuthClientCreate(OAuthClientBase):
    """Schema for creating a new OAuth client."""
    pass

class OAuthClientUpdate(BaseModel):
    """Schema for updating an OAuth client."""
    client_name: Optional[str] = None
    redirect_uris: Optional[List[str]] = None
    scopes: Optional[List[str]] = None
    is_confidential: Optional[bool] = None

    @field_validator("scopes")
    def validate_scopes(cls, v):
        """Validate scope values."""
        if v is None:
            return v
        return validate_scopes(v)

class OAuthClientInDBBase(OAuthClientBase):
    """Base schema for OAuth client data from database."""
    id: UUID4
    client_id: UUID4
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OAuthClient(OAuthClientInDBBase):
    """Schema for OAuth client data returned to client."""
    pass

class OAuthClientInDB(OAuthClientInDBBase):
    """Schema for OAuth client data stored in database (includes client secret)."""
    client_secret: str

class ClientRegistrationRequest(BaseModel):
    """Schema for client registration request."""
    client_name: str
    redirect_uris: str
    grant_types: str = "authorization_code refresh_token"
    response_types: str = "code"
    scopes: str
    client_uri: Optional[HttpUrl] = None
    logo_uri: Optional[HttpUrl] = None
    tos_uri: Optional[HttpUrl] = None
    policy_uri: Optional[HttpUrl] = None
    jwks_uri: Optional[HttpUrl] = None
    software_id: Optional[str] = None
    software_version: Optional[str] = None
    
    @field_validator("redirect_uris")
    def validate_redirect_uris(cls, v):
        """Convert redirect_uris string to list."""
        if isinstance(v, str):
            return v.split()
        return v
        
    @field_validator("grant_types")
    def validate_grant_types(cls, v):
        """Convert grant_types string to list."""
        if isinstance(v, str):
            return v.split()
        return v
        
    @field_validator("response_types")
    def validate_response_types(cls, v):
        """Convert response_types string to list."""
        if isinstance(v, str):
            return v.split()
        return v
        
    @field_validator("scopes")
    def validate_scopes(cls, v):
        """Convert scopes string to list."""
        if isinstance(v, str):
            return v.split()
        return v

class ClientRegistrationResponse(BaseModel):
    """Schema for client registration response."""
    client_id: str
    client_secret: str
    client_id_issued_at: int
    client_secret_expires_at: int
    redirect_uris: List[str]
    grant_types: List[str]
    response_types: List[str]
    client_name: str
    scopes: List[str]
    
    @field_validator("grant_types", "response_types", "redirect_uris", "scopes")
    def validate_list_fields(cls, v):
        """Ensure list fields are properly formatted."""
        if isinstance(v, str):
            return v.split()
        return v

class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    scope: str

class OAuthClientRegisterResponse(BaseModel):
    """Schema for OAuth client registration response."""
    client_id: UUID4
    client_secret: str
    client_name: str
    redirect_uris: List[str]
    scopes: List[str]
    is_confidential: bool

class AuthorizationRequest(BaseModel):
    """Schema for OAuth authorization request."""
    response_type: str
    client_id: UUID4
    redirect_uri: str
    scope: str
    state: str
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None

    @field_validator("response_type")
    def validate_response_type(cls, v):
        """Validate response_type value."""
        return validate_response_type(v)

    @field_validator("code_challenge_method")
    def validate_code_challenge_method(cls, v):
        """Validate code_challenge_method value."""
        return validate_code_challenge_method(v)

class TokenRequest(BaseModel):
    """Schema for OAuth token request."""
    grant_type: str
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    client_id: UUID4
    client_secret: Optional[str] = None
    code_verifier: Optional[str] = None
    refresh_token: Optional[str] = None

    @field_validator("grant_type")
    def validate_grant_type(cls, v):
        """Validate grant_type value."""
        return validate_grant_type(v)

class TokenResponse(BaseModel):
    """Schema for OAuth token response."""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: str
