from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

from mcp.server.fastmcp import FastMCP, Context

from app.models.memory import Memory, MemoryPermission
from app.models.user import User
from app.utils.embeddings import create_embedding
from app.endpoints.memories import get_user_from_token

def register_llm_endpoints(mcp: FastMCP):
    """Register LLM endpoints with MCP server"""
    
    @mcp.tool()
    async def query_user(user_id: int, prompt: str, ctx: Context) -> Dict[str, Any]:
        """
        Query an LLM with a prompt using a persona based on a user's public memories.
        
        Args:
            user_id: The ID of the user whose persona to use
            prompt: The prompt to send to the LLM
            
        Returns:
            Dictionary with LLM response
        """
        # Get authenticated user from token
        auth_user = await get_user_from_token(ctx)
        if not auth_user:
            return {"error": "Unauthorized"}
        
        # Get database session from context
        db = ctx.request_context.lifespan_context.db
        
        # Find target user in database
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalars().first()
        
        if not user:
            return {"error": f"User not found with ID: {user_id}"}
        
        # Find public memories for target user
        memories_result = await db.execute(
            select(Memory).where(
                (Memory.user_id == user_id) & 
                (Memory.permission == MemoryPermission.PUBLIC.value)
            )
        )
        memories = memories_result.scalars().all()
        
        if not memories:
            return {"error": f"No public memories found for user with ID: {user_id}"}
        
        # Combine memories into a single context
        memory_texts = [memory.text for memory in memories]
        memory_context = "\n\n".join(memory_texts)
        
        # Create LLM chain with LangChain
        llm = ChatOpenAI()
        
        # Create prompt template
        template = """
        You are an AI assistant that embodies the persona of a user based on their memories.
        
        Here are the memories that define this user's persona:
        
        {memory_context}
        
        Based on these memories, respond to the following prompt as if you were this user:
        
        {prompt}
        """
        
        prompt_template = PromptTemplate.from_template(template)
        
        # Create chain
        chain = (
            prompt_template 
            | llm 
            | StrOutputParser()
        )
        
        # Run chain
        response = await chain.ainvoke({
            "memory_context": memory_context,
            "prompt": prompt
        })
        
        # Return response
        return {
            "user_id": user_id,
            "username": user.username,
            "prompt": prompt,
            "response": response
        }
