import pytest
from fastapi.testclient import TestClient

def test_app_exists(test_app):
    """Test that the FastAPI app exists."""
    assert test_app is not None
    
def test_app_routes(test_app):
    """Test that the app has the expected routes."""
    routes = [route.path for route in test_app.routes]
    print("Available routes:", routes)  # Print routes for debugging
    assert "/" in routes
    assert "/health/" in routes  # Note the trailing slash
    assert "/docs" in routes
