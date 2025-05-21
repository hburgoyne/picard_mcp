"""
Health check API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.utils.logger import logger
import psutil
import time
from app.core.config import settings

router = APIRouter()

@router.get("/", summary="Health check endpoint")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint to verify that the service is running correctly.
    
    Returns:
        dict: Health status information
    """
    start_time = time.time()
    health_info = {
        "status": "healthy",
        "timestamp": start_time,
        "version": "0.1.0",
        "service": settings.PROJECT_NAME,
    }
    
    # Check database connection
    try:
        # Execute a simple query using SQLAlchemy text construct
        db.execute(text("SELECT 1"))
        health_info["database"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_info["status"] = "degraded"
        health_info["database"] = "disconnected"
        health_info["database_error"] = str(e)
    
    # Add system information
    try:
        health_info["system"] = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent
        }
    except Exception as e:
        logger.error(f"System info check failed: {str(e)}")
        health_info["system"] = {"error": str(e)}
    
    # Calculate response time
    health_info["response_time_ms"] = int((time.time() - start_time) * 1000)
    
    # Log health check
    log_level = "info" if health_info["status"] == "healthy" else "warning"
    getattr(logger, log_level)(f"Health check: {health_info['status']}")
    
    return health_info

@router.get("/readiness", summary="Readiness probe endpoint")
async def readiness():
    """
    Kubernetes readiness probe endpoint.
    
    Returns:
        dict: Readiness status
    """
    return {"status": "ready"}

@router.get("/liveness", summary="Liveness probe endpoint")
async def liveness():
    """
    Kubernetes liveness probe endpoint.
    
    Returns:
        dict: Liveness status
    """
    return {"status": "alive"}
