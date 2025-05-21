from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional, Dict, Any
import logging

from app.db.session import get_db
from app.models.memory import Memory
from app.models.user import User
from app.api.deps import get_current_user_with_memory_read
from app.schemas.mcp import QueryMemoryRequest as MemoryQueryRequest, MCPToolResponse as MemoryQueryResponse
from app.utils.langchain_utils import query_memories_with_langchain

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/query", response_model=MemoryQueryResponse)
async def query_memories(
    query_request: MemoryQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_with_memory_read)
):
    """
    Query memories using LangChain and LLM.
    """
    try:
        # Query memories using LangChain
        response = await query_memories_with_langchain(
            query=query_request.query,
            user_id=str(current_user.id),
            db=db,
            persona=query_request.persona,
            max_tokens=query_request.max_tokens,
            temperature=query_request.temperature
        )
        
        return MemoryQueryResponse(
            query=query_request.query,
            response=response,
            persona=query_request.persona
        )
    except Exception as e:
        logger.error(f"Error querying memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying memories: {str(e)}"
        )
