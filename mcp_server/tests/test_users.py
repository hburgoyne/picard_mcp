import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.utils.security import create_access_token

@pytest.fixture
def auth_headers():
    """Create authentication headers for test user."""
    # Create access token for test user
    access_token = create_access_token(
        data={"sub": "1", "scopes": ["profile:read"]}
    )
    return {"Authorization": f"Bearer {access_token}"}

def test_create_user(client: TestClient):
    """Test creating a user."""
    user_data = {
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "testpassword",
        "full_name": "Test User"
    }
    
    response = client.post("/users/", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    
    # Password should not be returned
    assert "password" not in data
    assert "hashed_password" not in data
    
    return data["id"]

def test_read_users_me(client: TestClient, auth_headers):
    """Test reading current user."""
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "username" in data
    assert "email" in data
    assert "full_name" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_update_user_me(client: TestClient, auth_headers):
    """Test updating current user."""
    update_data = {
        "full_name": "Updated Test User"
    }
    
    response = client.put("/users/me", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == update_data["full_name"]
    
    # Check that the user was actually updated
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == update_data["full_name"]
