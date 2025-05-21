from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Optional
import uuid
from datetime import datetime

from app.db.session import get_db
from app.models.memory import Memory
from app.schemas.memory import (
    MemoryCreate, 
    MemoryUpdate, 
    MemoryResponse,
    MemorySearchResults
)
from app.api.deps import (
    get_current_user_with_memory_read,
    get_current_user_with_memory_write
)
from app.models.user import User
from app.utils.embeddings import get_embedding
from app.utils.encryption import encrypt_text, decrypt_text

router = APIRouter()

@router.post("/", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    memory: MemoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_with_memory_write)
):
    """
    Create a new memory for the current user.
    """
    # Generate embedding for the memory text
    embedding = await get_embedding(memory.text)
    
    # Create new memory
    encrypted_text = None
    if memory.encrypt:
        encrypted_text = encrypt_text(memory.text)
    
    db_memory = Memory(
        user_id=current_user.id,
        text=memory.text,
        encrypted_text=encrypted_text,
        permission=memory.permission,
        embedding=embedding,
        expiration_date=memory.expiration_date
    )
    
    db.add(db_memory)
    await db.commit()
    await db.refresh(db_memory)
    
    return db_memory

@router.get("/", response_model=List[MemoryResponse])
async def read_memories(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_with_memory_read)
):
    """
    Retrieve all memories for the current user.
    """
    query = select(Memory).filter(
        Memory.user_id == current_user.id,
        (Memory.expiration_date.is_(None) | (Memory.expiration_date > datetime.utcnow()))
    ).offset(skip).limit(limit)
    
    result = await db.execute(query)
    memories = result.scalars().all()
    
    return memories

@router.get("/search", response_model=MemorySearchResults)
async def search_memories(
    query: str,
    limit: int = 5,
    threshold: float = 0.7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_with_memory_read)
):
    """
    Search memories using semantic similarity.
    """
    # Generate embedding for the query
    query_embedding = await get_embedding(query)
    
    # Perform vector similarity search
    # We use the dot product as similarity measure
    similarity_query = select(
        Memory,
        func.dot(Memory.embedding, query_embedding).label("similarity")
    ).filter(
        Memory.user_id == current_user.id,
        (Memory.expiration_date.is_(None) | (Memory.expiration_date > datetime.utcnow()))
    ).order_by(
        func.dot(Memory.embedding, query_embedding).desc()
    ).limit(limit)
    
    result = await db.execute(similarity_query)
    
    # Filter results by similarity threshold
    memories_with_scores = [(memory, float(similarity)) for memory, similarity in result if similarity >= threshold]
    
    return MemorySearchResults(
        query=query,
        results=memories_with_scores
    )

@router.get("/{memory_id}", response_model=MemoryResponse)
async def read_memory(
    memory_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_with_memory_read)
):
    """
    Get a specific memory by ID.
    """
    query = select(Memory).filter(Memory.id == memory_id)
    result = await db.execute(query)
    memory = result.scalars().first()
    
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    # Check if user has permission to access this memory
    if memory.user_id != current_user.id and memory.permission != "public":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this memory"
        )
    
    # Check if memory has expired
    if memory.expiration_date and memory.expiration_date < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory has expired"
        )
    
    return memory

@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: uuid.UUID,
    memory_update: MemoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_with_memory_write)
):
    """
    Update a memory.
    """
    query = select(Memory).filter(Memory.id == memory_id)
    result = await db.execute(query)
    memory = result.scalars().first()
    
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    # Check if user has permission to update this memory
    if memory.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this memory"
        )
    
    # Update memory fields
    if memory_update.text is not None:
        memory.text = memory_update.text
        # Update embedding if text changed
        memory.embedding = await get_embedding(memory_update.text)
        
        # Update encrypted text if needed
        if memory_update.encrypt:
            memory.encrypted_text = encrypt_text(memory_update.text)
        elif memory_update.encrypt is False:
            memory.encrypted_text = None
    
    if memory_update.permission is not None:
        memory.permission = memory_update.permission
    
    if memory_update.expiration_date is not None:
        memory.expiration_date = memory_update.expiration_date
    
    await db.commit()
    await db.refresh(memory)
    
    return memory

@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_with_memory_write)
):
    """
    Delete a memory.
    """
    query = select(Memory).filter(Memory.id == memory_id)
    result = await db.execute(query)
    memory = result.scalars().first()
    
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    # Check if user has permission to delete this memory
    if memory.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this memory"
        )
    
    await db.delete(memory)
    await db.commit()
    
    return None
