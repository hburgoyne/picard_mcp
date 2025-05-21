from langchain.llms import OpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
import logging
from typing import List, Dict, Any, Optional
import asyncio

from app.core.config import settings
from app.models.memory import Memory
from app.utils.embeddings import get_embedding

logger = logging.getLogger(__name__)

# Define persona templates
PERSONA_TEMPLATES = {
    "default": """You are a helpful assistant that answers questions based on the user's memories.
    
Memories:
{memories}

User Query: {query}

Your response should be helpful, relevant, and based on the memories provided. If the memories don't contain relevant information, you can say so.
""",
    "concise": """You are a concise assistant that provides brief answers based on the user's memories.
    
Memories:
{memories}

User Query: {query}

Provide a brief and direct response based on these memories. Be concise.
""",
    "creative": """You are a creative assistant that generates imaginative responses based on the user's memories.
    
Memories:
{memories}

User Query: {query}

Provide a creative and engaging response that incorporates these memories in an interesting way.
"""
}

async def get_relevant_memories(
    query: str,
    user_id: str,
    db: AsyncSession,
    limit: int = settings.MEMORY_K
) -> List[Memory]:
    """
    Retrieve memories relevant to the query using vector similarity search.
    
    Args:
        query: The user's query
        user_id: The user's ID
        db: Database session
        limit: Maximum number of memories to retrieve
        
    Returns:
        List of relevant Memory objects
    """
    # Generate embedding for the query
    query_embedding = await get_embedding(query)
    
    # Perform vector similarity search
    similarity_query = select(
        Memory,
        func.dot(Memory.embedding, query_embedding).label("similarity")
    ).filter(
        Memory.user_id == user_id
    ).order_by(
        func.dot(Memory.embedding, query_embedding).desc()
    ).limit(limit)
    
    result = await db.execute(similarity_query)
    
    # Extract memories from results
    memories = [memory for memory, _ in result]
    
    return memories

async def query_memories_with_langchain(
    query: str,
    user_id: str,
    db: AsyncSession,
    persona: str = "default",
    max_tokens: int = 500,
    temperature: float = 0.7
) -> str:
    """
    Query memories using LangChain and LLM.
    
    Args:
        query: The user's query
        user_id: The user's ID
        db: Database session
        persona: The persona to use for the response
        max_tokens: Maximum number of tokens in the response
        temperature: Temperature for the LLM
        
    Returns:
        LLM response based on relevant memories
    """
    # Get relevant memories
    memories = await get_relevant_memories(query, user_id, db)
    
    if not memories:
        return "I couldn't find any relevant memories to answer your question."
    
    # Format memories as text
    memories_text = "\n".join([f"- {memory.text}" for memory in memories])
    
    # Get the appropriate template for the persona
    template = PERSONA_TEMPLATES.get(persona, PERSONA_TEMPLATES["default"])
    
    # Create prompt template
    prompt = PromptTemplate(
        input_variables=["memories", "query"],
        template=template
    )
    
    # Initialize LLM
    llm = ChatOpenAI(
        model_name=settings.LLM_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        openai_api_key=settings.OPENAI_API_KEY
    )
    
    # Create chain
    chain = LLMChain(llm=llm, prompt=prompt)
    
    # Run chain
    response = chain.run(memories=memories_text, query=query)
    
    return response
