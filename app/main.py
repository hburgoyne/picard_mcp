import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.auth import AuthSettings, RevocationOptions, ClientRegistrationOptions

from app.config import settings
from app.database import init_db, close_db
from app.auth.provider import PicardOAuthProvider
from app.models import AppContext

# Create FastAPI app
app = FastAPI(title="Picard MCP Server")

# Create MCP server with OAuth2 authentication
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with database connection"""
    # Initialize database on startup
    db = await init_db()
    try:
        yield AppContext(db=db)
    finally:
        # Close database connection on shutdown
        await close_db(db)

# Configure MCP server with OAuth2
mcp = FastMCP(
    settings.MCP_SERVER_NAME,
    lifespan=app_lifespan,
    auth_server_provider=PicardOAuthProvider(),
    auth=AuthSettings(
        issuer_url=settings.MCP_ISSUER_URL,
        revocation_options=RevocationOptions(
            enabled=True,
        ),
        client_registration_options=ClientRegistrationOptions(
            enabled=True,
            valid_scopes=["memories:read", "memories:write", "memories:admin"],
            default_scopes=["memories:read", "memories:write"],
        ),
        required_scopes=["memories:read"],
    ),
)

# Import and register endpoints
from app.endpoints.memories import register_memory_endpoints
from app.endpoints.llm import register_llm_endpoints

# Register endpoints with MCP server
register_memory_endpoints(mcp)
register_llm_endpoints(mcp)

# Mount MCP server to FastAPI app
app.mount("/", mcp.app)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.MCP_SERVER_HOST,
        port=settings.MCP_SERVER_PORT,
        reload=True
    )
