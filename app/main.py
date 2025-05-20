import os
import sys
import traceback
from contextlib import asynccontextmanager
from typing import AsyncIterator

# Add detailed debugging to see what's happening during import
print("Starting app.main import")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Environment variables: {os.environ}")

# Make sure the current directory is in the Python path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(f"Adding to Python path: {base_dir}")
sys.path.insert(0, base_dir)
print(f"Python path: {sys.path}")

# Import FastAPI first to isolate potential issues
try:
    from fastapi import FastAPI
    print("Successfully imported FastAPI")
except ImportError as e:
    print(f"Error importing FastAPI: {e}")
    traceback.print_exc()
    raise

# Try importing MCP modules with detailed error handling
try:
    print("Attempting to import MCP modules...")
    from mcp.server.fastmcp import FastMCP, Context
    print("Successfully imported FastMCP and Context")
    from mcp.server.auth.settings import AuthSettings, RevocationOptions, ClientRegistrationOptions
    print("Successfully imported all MCP modules")
except ImportError as e:
    print(f"Error importing MCP modules: {e}")
    traceback.print_exc()
    raise
except Exception as e:
    print(f"Unexpected error during import: {type(e).__name__}: {e}")
    traceback.print_exc()
    raise

# Import app modules with error handling
try:
    print("Importing app modules...")
    from app.config import settings
    print("Successfully imported settings")
    print(f"MCP_SERVER_NAME: {settings.MCP_SERVER_NAME}")
    print(f"MCP_ISSUER_URL: {settings.MCP_ISSUER_URL}")
    
    from app.database import init_db, close_db
    print("Successfully imported database functions")
    
    from app.auth.provider import PicardOAuthProvider
    print("Successfully imported PicardOAuthProvider")
    
    from app.models import AppContext
    print("Successfully imported all app modules")
except Exception as e:
    print(f"Error importing app modules: {type(e).__name__}: {e}")
    traceback.print_exc()
    raise

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
        # Remove required_scopes to allow any combination of valid scopes
        required_scopes=[], 
    ),
)

# Import and register endpoints
from app.endpoints.memories import register_memory_endpoints
from app.endpoints.llm import register_llm_endpoints

# Register endpoints with MCP server
register_memory_endpoints(mcp)
register_llm_endpoints(mcp)

# Mount MCP server to FastAPI app
# Mount at root to handle all paths
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
