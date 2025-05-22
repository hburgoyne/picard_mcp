"""
Main API router that includes all endpoint routers.
"""
from fastapi import APIRouter
from app.api.endpoints import health, oauth, admin

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(oauth.router, prefix="/oauth", tags=["OAuth"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
