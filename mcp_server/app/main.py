from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_server")

# Create FastAPI app
app = FastAPI(
    title=os.getenv("MCP_SERVER_NAME", "Picard MCP"),
    description="Model Context Protocol (MCP) server for memory management",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to Picard MCP Server",
        "documentation": "/docs",
    }

# Import and include API router
from app.api.api import api_router
app.include_router(api_router)

# Database initialization
from app.db.utils import initialize_db
from app.db.session import AsyncSessionLocal

@app.on_event("startup")
async def startup_db_client():
    """Initialize database on startup"""
    try:
        async with AsyncSessionLocal() as session:
            await initialize_db(session)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("MCP_SERVER_HOST", "0.0.0.0"),
        port=int(os.getenv("MCP_SERVER_PORT", "8000")),
        reload=True,
    )
