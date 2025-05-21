from fastapi import APIRouter
import importlib
import logging

api_router = APIRouter()
logger = logging.getLogger(__name__)

# List of endpoint modules to include
endpoint_modules = ["health", "oauth", "memories", "users", "llm"]

# Include available endpoint routers
for module_name in endpoint_modules:
    try:
        module = importlib.import_module(f"app.api.endpoints.{module_name}")
        api_router.include_router(
            module.router,
            prefix=f"/{module_name}",
            tags=[module_name.capitalize()]
        )
        logger.info(f"Loaded endpoint module: {module_name}")
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not load endpoint module {module_name}: {e}")
        # Continue loading other modules even if one fails
