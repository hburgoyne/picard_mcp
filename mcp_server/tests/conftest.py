import pytest
import os
import sys

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import app for direct testing
from app.main import app

@pytest.fixture
def test_app():
    """Return the FastAPI app for testing."""
    return app
