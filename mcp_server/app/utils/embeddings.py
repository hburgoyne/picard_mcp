from openai import OpenAI
from typing import List, Optional
import numpy as np
import asyncio
import logging
from app.core.config import settings

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

logger = logging.getLogger(__name__)

async def get_embedding_async(text: str) -> Optional[List[float]]:
    """
    Get embedding vector for text using OpenAI's embedding model asynchronously.
    Returns a list of floats representing the embedding vector.
    """
    if not text or not text.strip():
        return None
    
    try:
        # Run the synchronous OpenAI call in a thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.embeddings.create(
                input=text.strip(),
                model=settings.EMBEDDING_MODEL
            )
        )
        
        # Extract embedding from response
        embedding = response.data[0].embedding
        return embedding
    except Exception as e:
        logger.error(f"Error getting embedding for text '{text[:50]}...': {e}")
        raise RuntimeError(f"Failed to generate embedding: {str(e)}")

def get_embedding(text: str) -> Optional[List[float]]:
    """
    Get embedding vector for text using OpenAI's embedding model (synchronous version).
    Returns a list of floats representing the embedding vector.
    """
    if not text or not text.strip():
        return None
    
    try:
        # Call OpenAI API to get embedding
        response = client.embeddings.create(
            input=text.strip(),
            model=settings.EMBEDDING_MODEL
        )
        
        # Extract embedding from response
        embedding = response.data[0].embedding
        return embedding
    except Exception as e:
        logger.error(f"Error getting embedding for text '{text[:50]}...': {e}")
        raise RuntimeError(f"Failed to generate embedding: {str(e)}")

def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate cosine similarity between two embedding vectors.
    Returns a float between -1 and 1, where 1 means identical vectors.
    """
    if not embedding1 or not embedding2:
        return 0.0
    
    # Convert to numpy arrays
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    # Calculate cosine similarity
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    # Avoid division by zero
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)

async def search_memories_by_embedding(
    db,
    user_id: str,
    query_embedding: List[float],
    limit: int = 10,
    similarity_threshold: float = 0.5,
    permission_filter: Optional[str] = None
) -> List[dict]:
    """
    Search memories using vector similarity with pgvector.
    Returns memories ordered by cosine similarity.
    """
    from app.models.memory import Memory
    from sqlalchemy import text
    import asyncio
    
    try:
        # Build the query with pgvector cosine similarity
        query_vector_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        # Base query for cosine similarity using pgvector
        sql_query = """
        SELECT 
            id, text, permission, created_at, updated_at, expiration_date,
            1 - (embedding <=> %s::vector) as similarity
        FROM memories 
        WHERE user_id = %s 
        AND embedding IS NOT NULL
        AND (1 - (embedding <=> %s::vector)) >= %s
        """
        
        params = [query_vector_str, str(user_id), query_vector_str, similarity_threshold]
        
        # Add permission filter if specified
        if permission_filter:
            sql_query += " AND permission = %s"
            params.append(permission_filter)
        
        # Order by similarity and limit
        sql_query += " ORDER BY similarity DESC LIMIT %s"
        params.append(limit)
        
        # Execute the query in a thread pool since it's synchronous
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: db.execute(text(sql_query), params)
        )
        memories = result.fetchall()
        
        # Convert to list of dictionaries
        memory_list = []
        for memory in memories:
            memory_dict = {
                "id": str(memory.id),
                "text": memory.text,
                "permission": memory.permission,
                "created_at": memory.created_at.isoformat(),
                "updated_at": memory.updated_at.isoformat(),
                "similarity": float(memory.similarity),
                "expiration_date": memory.expiration_date.isoformat() if memory.expiration_date else None
            }
            memory_list.append(memory_dict)
        
        return memory_list
        
    except Exception as e:
        logger.error(f"Error searching memories by embedding: {e}")
        raise RuntimeError(f"Failed to search memories: {str(e)}")
