"""
ASGI configuration for the MCP server.

This is used for production with Uvicorn.
"""
import os
from app.main import app
import uvicorn
from app.utils.logger import logger

if __name__ == "__main__":
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_SERVER_PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    logger.info(f"Starting ASGI server at {host}:{port} with log level {log_level}")
    
    uvicorn.run(
        "asgi:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=False,
        workers=int(os.getenv("WORKERS", "1")),
        limit_concurrency=int(os.getenv("LIMIT_CONCURRENCY", "100")),
        limit_max_requests=int(os.getenv("LIMIT_MAX_REQUESTS", "10000")),
    )
