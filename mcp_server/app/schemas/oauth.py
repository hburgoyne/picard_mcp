from pydantic import BaseModel, UUID4, Field, validator, HttpUrl
from typing import Optional, List, Union
from datetime import datetime
import uuid

class OAuthClientBase(BaseModel):
    """Base schema for OAuth client data."""
    client_name: str
    redirect_uris: List[str]
    scopes: List[str]
    is_confidential: bool = True

    @validator("scopes")
    def validate_scopes(cls, v):
        """Validate scope values."""
        allowed_scopes = ["memories:read", "memories:write", "memories:admin"]
        for scope in v:
            if scope not in allowed_scopes:
                raise ValueError(f"Scope must be one of: {', '.join(allowed_scopes)}")
        return v

class OAuthClientCreate(OAuthClientBase):
    """Schema for creating a new OAuth client."""
    pass

class OAuthClientUpdate(BaseModel):
    """Schema for updating an OAuth client."""
    client_name: Optional[str] = None
    redirect_uris: Optional[List[str]] = None
    scopes: Optional[List[str]] = None
    is_confidential: Optional[bool] = None

    @validator("scopes")
    def validate_scopes(cls, v):
        """Validate scope values."""
        if v is None:
            return v
        allowed_scopes = ["memories:read", "memories:write", "memories:admin"]
        for scope in v:
            if scope not in allowed_scopes:
                raise ValueError(f"Scope must be one of: {', '.join(allowed_scopes)}")
        return v

class OAuthClientInDBBase(OAuthClientBase):
    """Base schema for OAuth client data from database."""
    id: UUID4
    client_id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class OAuthClient(OAuthClientInDBBase):
    """Schema for OAuth client data returned to client."""
    pass

class OAuthClientInDB(OAuthClientInDBBase):
    """Schema for OAuth client data stored in database (includes client secret)."""
    client_secret: str

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

    @validator("response_type")
    def validate_response_type(cls, v):
        """Validate response_type value."""
        if v != "code":
            raise ValueError("response_type must be 'code'")
        return v

    @validator("code_challenge_method")
    def validate_code_challenge_method(cls, v):
        """Validate code_challenge_method value."""
        if v is not None and v != "S256":
            raise ValueError("code_challenge_method must be 'S256'")
        return v

class TokenRequest(BaseModel):
    """Schema for OAuth token request."""
    grant_type: str
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    client_id: UUID4
    client_secret: Optional[str] = None
    code_verifier: Optional[str] = None
    refresh_token: Optional[str] = None

    @validator("grant_type")
    def validate_grant_type(cls, v):
        """Validate grant_type value."""
        allowed_grant_types = ["authorization_code", "refresh_token"]
        if v not in allowed_grant_types:
            raise ValueError(f"grant_type must be one of: {', '.join(allowed_grant_types)}")
        return v

class TokenResponse(BaseModel):
    """Schema for OAuth token response."""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: str

# Add these schema classes for client registration
class ClientRegistrationRequest(BaseModel):
    """Schema for client registration request."""
    client_name: str
    redirect_uris: List[str]
    grant_types: Optional[List[str]] = ["authorization_code", "refresh_token"]
    response_types: Optional[List[str]] = ["code"]
    scopes: List[str]
    client_uri: Optional[str] = None
    logo_uri: Optional[str] = None
    tos_uri: Optional[str] = None
    policy_uri: Optional[str] = None
    jwks_uri: Optional[str] = None
    software_id: Optional[str] = None
    software_version: Optional[str] = None

    @validator("scopes")
    def validate_scopes(cls, v):
        """Validate scope values."""
        allowed_scopes = ["memories:read", "memories:write", "memories:admin"]
        for scope in v:
            if scope not in allowed_scopes:
                raise ValueError(f"Scope must be one of: {', '.join(allowed_scopes)}")
        return v

class ClientRegistrationResponse(BaseModel):
    """Schema for client registration response."""
    client_id: str
    client_secret: str
    client_id_issued_at: int
    client_secret_expires_at: int
