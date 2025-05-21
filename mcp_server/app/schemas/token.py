from pydantic import BaseModel, UUID4
from typing import Optional, List

class Token(BaseModel):
    """Schema for access token."""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: str

class TokenData(BaseModel):
    """Schema for token payload data."""
    sub: Optional[str] = None
    scopes: List[str] = []
    user_id: Optional[UUID4] = None
    exp: Optional[int] = None
    iat: Optional[int] = None
    iss: Optional[str] = None
    jti: Optional[str] = None
    token_type: Optional[str] = None
