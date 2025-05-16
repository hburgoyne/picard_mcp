from typing import List, Dict, Any, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from mcp.server.fastmcp import FastMCP, Context

from app.models.memory import Memory, MemoryPermission
from app.models.user import User
from app.utils.embeddings import create_embedding

async def get_user_from_token(ctx: Context) -> Optional[User]:
    """Get user from token"""
    # Get token information from context
    token_info = ctx.request_context.auth_info
    if not token_info or not token_info.active:
        return None
    
    # Get user ID from token
    user_id = int(token_info.sub)
    
    # Get database session from context
    db = ctx.request_context.lifespan_context.db
    
    # Find user in database
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalars().first()
    
    return user

def register_memory_endpoints(mcp: FastMCP):
    """Register memory endpoints with MCP server"""
    
    @mcp.tool()
    async def submit_memory(text: str, ctx: Context) -> Dict[str, Any]:
        """
        Submit a new memory for the authenticated user.
        
        Args:
            text: The text content of the memory
            
        Returns:
            Dictionary with memory information
        """
        # Get user from token
        user = await get_user_from_token(ctx)
        if not user:
            return {"error": "Unauthorized"}
        
        # Get database session from context
        db = ctx.request_context.lifespan_context.db
        
        # Create embedding for text
        embedding = await create_embedding(text)
        
        # Create memory
        memory = Memory(
            user_id=user.id,
            text=text,
            embedding=embedding,
            permission=MemoryPermission.PRIVATE.value
        )
        db.add(memory)
        await db.commit()
        await db.refresh(memory)
        
        # Return memory information
        return memory.to_dict()
    
    @mcp.tool()
    async def retrieve_memories(ctx: Context) -> List[Dict[str, Any]]:
        """
        Retrieve all memories for the authenticated user.
        
        Returns:
            List of dictionaries with memory information
        """
        # Get user from token
        user = await get_user_from_token(ctx)
        if not user:
            return {"error": "Unauthorized"}
        
        # Get database session from context
        db = ctx.request_context.lifespan_context.db
        
        # Find memories in database
        memories_result = await db.execute(
            select(Memory).where(Memory.user_id == user.id)
        )
        memories = memories_result.scalars().all()
        
        # Return memories
        return [memory.to_dict() for memory in memories]
    
    @mcp.tool()
    async def modify_permissions(memory_id: int, permission: str, ctx: Context) -> Dict[str, Any]:
        """
        Modify the permissions of a memory.
        
        Args:
            memory_id: The ID of the memory to modify
            permission: The new permission value (public or private)
            
        Returns:
            Dictionary with updated memory information
        """
        # Get user from token
        user = await get_user_from_token(ctx)
        if not user:
            return {"error": "Unauthorized"}
        
        # Validate permission value
        if permission not in [MemoryPermission.PUBLIC.value, MemoryPermission.PRIVATE.value]:
            return {"error": f"Invalid permission value: {permission}"}
        
        # Get database session from context
        db = ctx.request_context.lifespan_context.db
        
        # Find memory in database
        memory_result = await db.execute(
            select(Memory).where(
                (Memory.id == memory_id) & 
                (Memory.user_id == user.id)
            )
        )
        memory = memory_result.scalars().first()
        
        if not memory:
            return {"error": f"Memory not found with ID: {memory_id}"}
        
        # Update memory permission
        memory.permission = permission
        await db.commit()
        await db.refresh(memory)
        
        # Return updated memory
        return memory.to_dict()
    
    @mcp.resource("memories://{user_id}/public")
    async def get_public_memories(user_id: int) -> List[Dict[str, Any]]:
        """
        Get public memories for a specific user.
        
        Args:
            user_id: The ID of the user to get public memories for
            
        Returns:
            List of dictionaries with memory information
        """
        # Get database session
        from app.database import get_db
        async for db in get_db():
            # Find public memories in database
            memories_result = await db.execute(
                select(Memory).where(
                    (Memory.user_id == user_id) & 
                    (Memory.permission == MemoryPermission.PUBLIC.value)
                )
            )
            memories = memories_result.scalars().all()
            
            # Return public memories
            return [memory.to_dict() for memory in memories]
        
        # If we couldn't get a database session
        return []
