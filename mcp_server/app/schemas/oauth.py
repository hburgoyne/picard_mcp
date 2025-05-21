from pydantic import BaseModel, UUID4, Field, field_validator, HttpUrl, validator
from typing import Optional, List, Union
from datetime import datetime
import uuid

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
