from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from dotenv import load_dotenv
from app.utils.logger import logger, setup_logger
from app.core.config import settings
import time
import uuid

# Load environment variables
load_dotenv()

# Set up application logger
app_logger = setup_logger("mcp_server", os.getenv("LOG_LEVEL", "INFO"))

# Log application startup
logger.info(f"Starting {settings.PROJECT_NAME} server")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Model Context Protocol (MCP) server for memory management",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Request ID middleware for tracing
@app.middleware("http")
async def add_request_id_middleware(request, call_next):
    """
    Middleware to add a unique request ID to each request for tracing.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Add request ID to the request state
    request.state.request_id = request_id
    
    # Log incoming request
    logger.info(f"Request started: {request.method} {request.url.path} (ID: {request_id})")
    
    # Process the request
    response = await call_next(request)
    
    # Calculate request duration
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log completed request
    logger.info(f"Request completed: {request.method} {request.url.path} - {response.status_code} in {process_time:.2f}ms (ID: {request_id})")
    
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} Server",
        "documentation": "/docs",
        "version": "0.1.0"
    }

# Import and include the API router
from app.api.api import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Start the application using Uvicorn if this file is run directly
if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting Uvicorn server at {settings.MCP_SERVER_HOST}:{settings.MCP_SERVER_PORT}")
    uvicorn.run(
        "app.main:app",
        host=os.getenv("MCP_SERVER_HOST", "0.0.0.0"),
        port=int(os.getenv("MCP_SERVER_PORT", "8000")),
        reload=True,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
