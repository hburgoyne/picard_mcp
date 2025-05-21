from pydantic import BaseModel, UUID4, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

class MCPToolRequest(BaseModel):
    """Base schema for MCP tool requests."""
    tool: str
    data: Dict[str, Any]

class MCPToolResponse(BaseModel):
    """Base schema for MCP tool responses."""
    status: str
    data: Dict[str, Any]

class MCPResourceRequest(BaseModel):
    """Base schema for MCP resource requests."""
    resource_uri: str

class MCPResourceResponse(BaseModel):
    """Base schema for MCP resource responses."""
    status: str
    data: Dict[str, Any]

# Memory Tool Schemas
class SubmitMemoryRequest(BaseModel):
    """Schema for submit_memory tool request."""
    text: str
    permission: str = "private"
    expiration_date: Optional[datetime] = None

class UpdateMemoryRequest(BaseModel):
    """Schema for update_memory tool request."""
    memory_id: UUID4
    text: str
    expiration_date: Optional[datetime] = None

class DeleteMemoryRequest(BaseModel):
    """Schema for delete_memory tool request."""
    memory_id: UUID4

class QueryMemoryRequest(BaseModel):
    """Schema for query_memory tool request."""
    query: str
    limit: int = 10

class QueryUserRequest(BaseModel):
    """Schema for query_user tool request."""
    user_id: UUID4
    prompt: str

class ModifyPermissionsRequest(BaseModel):
    """Schema for modify_permissions tool request."""
    memory_id: UUID4
    permission: str

class GetMemoriesRequest(BaseModel):
    """Schema for get_memories tool request."""
    user_id: Optional[UUID4] = None
    permission: Optional[str] = None
    expired: Optional[bool] = None

# Memory Resource Schemas
class MemoryResourceResponse(BaseModel):
    """Schema for memory resource response."""
    id: UUID4
    text: str
    permission: str
    user_id: UUID4
    created_at: datetime
    updated_at: datetime
    expiration_date: Optional[datetime] = None

class UserMemoriesResourceResponse(BaseModel):
    """Schema for user memories resource response."""
    user_id: UUID4
    memories: List[MemoryResourceResponse]
