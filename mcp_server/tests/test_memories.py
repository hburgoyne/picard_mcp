import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime, timedelta

from app.models.user import User
from app.utils.security import get_password_hash, create_access_token

@pytest.fixture
def auth_headers():
    """Create authentication headers for test user."""
    # Create access token for test user
    access_token = create_access_token(
        data={"sub": "1", "scopes": ["memories:read", "memories:write"]}
    )
    return {"Authorization": f"Bearer {access_token}"}

def test_create_memory(client: TestClient, auth_headers):
    """Test creating a memory."""
    memory_data = {
        "text": "This is a test memory",
        "permission": "private",
        "encrypt": False
    }
    
    response = client.post("/memories/", json=memory_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["text"] == memory_data["text"]
    assert data["permission"] == memory_data["permission"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    
    # Store memory ID for other tests
    memory_id = data["id"]
    return memory_id

def test_read_memories(client: TestClient, auth_headers):
    """Test reading all memories."""
    # First create a memory
    memory_id = test_create_memory(client, auth_headers)
    
    # Get all memories
    response = client.get("/memories/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Check that the created memory is in the list
    memory_ids = [memory["id"] for memory in data]
    assert memory_id in memory_ids

def test_read_memory(client: TestClient, auth_headers):
    """Test reading a specific memory."""
    # First create a memory
    memory_id = test_create_memory(client, auth_headers)
    
    # Get the memory
    response = client.get(f"/memories/{memory_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == memory_id
    assert data["text"] == "This is a test memory"
    assert data["permission"] == "private"

def test_update_memory(client: TestClient, auth_headers):
    """Test updating a memory."""
    # First create a memory
    memory_id = test_create_memory(client, auth_headers)
    
    # Update the memory
    update_data = {
        "text": "This is an updated test memory",
        "permission": "public"
    }
    
    response = client.put(f"/memories/{memory_id}", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == memory_id
    assert data["text"] == update_data["text"]
    assert data["permission"] == update_data["permission"]

def test_delete_memory(client: TestClient, auth_headers):
    """Test deleting a memory."""
    # First create a memory
    memory_id = test_create_memory(client, auth_headers)
    
    # Delete the memory
    response = client.delete(f"/memories/{memory_id}", headers=auth_headers)
    assert response.status_code == 204
    
    # Try to get the deleted memory
    response = client.get(f"/memories/{memory_id}", headers=auth_headers)
    assert response.status_code == 404

def test_search_memories(client: TestClient, auth_headers):
    """Test searching memories."""
    # First create some memories
    memory_data = [
        {"text": "I went to the park yesterday", "permission": "private", "encrypt": False},
        {"text": "I had pizza for dinner", "permission": "private", "encrypt": False},
        {"text": "The weather was nice today", "permission": "private", "encrypt": False}
    ]
    
    for data in memory_data:
        response = client.post("/memories/", json=data, headers=auth_headers)
        assert response.status_code == 201
    
    # Search for memories
    response = client.get("/memories/search?query=park", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "results" in data
    assert data["query"] == "park"
    
    # Check that the results contain the relevant memory
    found = False
    for memory, score in data["results"]:
        if "park" in memory["text"].lower():
            found = True
            break
    
    assert found, "Search did not return the expected memory"
