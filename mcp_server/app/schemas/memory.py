from pydantic import BaseModel, UUID4, Field, field_validator, ConfigDict
from typing import Optional, List, Union
from datetime import datetime
import uuid

def validate_permission(v: str) -> str:
    """Validate permission value."""
    allowed_permissions = ["private", "public"]
    if v is None:
        return v
    if v not in allowed_permissions:
        raise ValueError(f"Permission must be one of: {', '.join(allowed_permissions)}")
    return v

class MemoryBase(BaseModel):
    """Base schema for memory data."""
    text: str
    permission: str = "private"  # Default to private
    expiration_date: Optional[datetime] = None

    @field_validator("permission")
    def validate_permission(cls, v):
        """Validate permission value."""
        return validate_permission(v)

class MemoryCreate(MemoryBase):
    """Schema for creating a new memory."""
    encrypt: bool = False  # Whether to encrypt the memory text

class MemoryUpdate(BaseModel):
    """Schema for updating a memory."""
    text: Optional[str] = None
    permission: Optional[str] = None
    expiration_date: Optional[datetime] = None
    encrypt: Optional[bool] = None  # Whether to encrypt the memory text

    @field_validator("permission")
    def validate_permission(cls, v):
        """Validate permission value."""
        return validate_permission(v)

class MemoryInDBBase(MemoryBase):
    """Base schema for memory data from database."""
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime
    embedding: Optional[List[float]] = None

    model_config = ConfigDict(from_attributes=True)

class MemoryResponse(MemoryInDBBase):
    """Schema for memory data returned to client."""
    is_expired: bool
    
class Memory(MemoryResponse):
    """Alias for MemoryResponse for backward compatibility."""
    pass

class MemoryInDB(MemoryInDBBase):
    """Schema for memory data stored in database (includes encrypted text)."""
    encrypted_text: Optional[str] = None

class MemoryQuery(BaseModel):
    """Schema for querying memories."""
    query: str
    limit: int = 10

class MemoryPermissionUpdate(BaseModel):
    """Schema for updating memory permission."""
    memory_id: UUID4
    permission: str

    @field_validator("permission")
    def validate_permission(cls, v):
        """Validate permission value."""
        return validate_permission(v)

class MemoryWithScore(BaseModel):
    """Schema for memory with similarity score."""
    memory: MemoryResponse
    score: float

class MemorySearchResults(BaseModel):
    """Schema for memory search results."""
    query: str
    results: List[tuple[MemoryResponse, float]]
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
