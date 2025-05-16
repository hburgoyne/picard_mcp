import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

# Add debugging to see what's happening during import
print("Starting app.main import")

# Make sure the current directory is in the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI

# Try importing MCP modules with error handling
try:
    from mcp.server.fastmcp import FastMCP, Context
    from mcp.server.auth.settings import AuthSettings, RevocationOptions, ClientRegistrationOptions
    print("Successfully imported MCP modules")
except ImportError as e:
    print(f"Error importing MCP modules: {e}")
    raise

from app.config import settings
from app.database import init_db, close_db
from app.auth.provider import PicardOAuthProvider
from app.models import AppContext

# Create FastAPI app
app = FastAPI(title="Picard MCP Server")

# Add middleware to catch and log exceptions
@app.middleware("http")
async def catch_all_exceptions(request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        import traceback
        traceback.print_exc()
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

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
# In the latest version of FastMCP, we need to use the streamable_http_app method
app.mount("/", mcp.streamable_http_app())

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
