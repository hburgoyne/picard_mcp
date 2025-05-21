from fastapi import APIRouter

from app.api.endpoints import oauth, memories, users, health, llm

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(oauth.router, prefix="/oauth", tags=["OAuth"])
api_router.include_router(memories.router, prefix="/memories", tags=["Memories"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(llm.router, prefix="/llm", tags=["LLM"])
