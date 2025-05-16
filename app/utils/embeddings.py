from typing import List, Dict, Any
import numpy as np
from openai import OpenAI

from app.config import settings

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def create_embedding(text: str) -> List[float]:
    """Create embedding for text using OpenAI API"""
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding

async def similarity_search(query_embedding: List[float], embeddings: List[List[float]]) -> List[Dict[str, Any]]:
    """Search for similar embeddings using cosine similarity"""
    # Convert to numpy arrays
    query_embedding_np = np.array(query_embedding)
    embeddings_np = np.array(embeddings)
    
    # Calculate cosine similarity
    similarities = np.dot(embeddings_np, query_embedding_np) / (
        np.linalg.norm(embeddings_np, axis=1) * np.linalg.norm(query_embedding_np)
    )
    
    # Sort by similarity
    indices = np.argsort(similarities)[::-1]
    
    # Return sorted indices and similarities
    return [
        {"index": int(idx), "similarity": float(similarities[idx])}
        for idx in indices
    ]
