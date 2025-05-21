from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.utils import check_database_connection

router = APIRouter()

@router.get("/", summary="Health check endpoint")
async def health_check():
    """
    Basic health check endpoint that returns the status of the API.
    """
    return {"status": "healthy", "service": "mcp_server"}

@router.get("/db", summary="Database health check")
async def db_health_check(db: AsyncSession = Depends(get_db)):
    """
    Check if the database connection is working.
    """
    is_connected = await check_database_connection(db)
    return {"status": "healthy" if is_connected else "unhealthy", "database": "connected" if is_connected else "disconnected"}
