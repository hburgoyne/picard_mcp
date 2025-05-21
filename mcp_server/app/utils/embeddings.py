import openai
from typing import List, Optional
import numpy as np
from app.core.config import settings

# Set OpenAI API key
openai.api_key = settings.OPENAI_API_KEY

def get_embedding(text: str) -> Optional[List[float]]:
    """
    Get embedding vector for text using OpenAI's embedding model.
    Returns a list of floats representing the embedding vector.
    """
    if not text:
        return None
    
    try:
        # Call OpenAI API to get embedding
        response = openai.Embedding.create(
            input=text,
            model=settings.EMBEDDING_MODEL
        )
        
        # Extract embedding from response
        embedding = response['data'][0]['embedding']
        return embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

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
