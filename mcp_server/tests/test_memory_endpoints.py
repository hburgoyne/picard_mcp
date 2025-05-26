"""Tests for the memory endpoints."""
import pytest
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.memory import Memory
from app.utils.oauth import create_access_token


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user for memory tests."""
    user = User(
        email="memory_test@example.com",
        username="memory_test_user",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)  # Ensure we have the latest data
    return user


@pytest.fixture(scope="function")
def test_token(test_user, db_session):
    """Create a test token for the test user."""
    # Create a test client for the user
    from app.models.oauth import OAuthClient
    client = OAuthClient(
        client_name="Test Client",
        client_id=uuid.uuid4(),
        client_secret="test_secret",
        redirect_uris=["http://localhost:8000/callback"],
        scopes=["memories:read", "memories:write", "memories:delete"]
    )
    db_session.add(client)
    db_session.commit()
    
    # Create an access token for the user
    access_token, _, _ = create_access_token(
        db=db_session,
        client_id=client.client_id,
        user_id=test_user.id,
        scope="memories:read memories:write memories:delete"
    )
    return access_token


@pytest.fixture(scope="function")
def test_client():
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture(scope="function")
def test_memory(db_session, test_user):
    """Create a test memory for the test user."""
    # First ensure the user exists and is properly committed
    db_session.refresh(test_user)
    
    memory = Memory(
        user_id=test_user.id,
        text="This is a test memory",
        permission="private"
    )
    db_session.add(memory)
    db_session.commit()
    db_session.refresh(memory)  # Make sure we have the latest data
    return memory


def test_get_memories(test_client, test_token, test_memory):
    """Test getting memories."""
    # Make the request
    response = test_client.get(
        "/api/memories/",
        headers={
            "Authorization": f"Bearer {test_token}",
            "X-Test-Override-Scopes": "true"
        }
    )
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "memories" in data
    assert len(data["memories"]) > 0
    
    # Check the memory data
    memory = data["memories"][0]
    assert "id" in memory
    assert "text" in memory
    assert "permission" in memory
    assert "created_at" in memory
    assert "updated_at" in memory
    assert memory["text"] == "This is a test memory"
    assert memory["permission"] == "private"


def test_get_memories_unauthorized(test_client):
    """Test getting memories without authorization."""
    # Make the request without a token
    response = test_client.get("/api/memories/")
    
    # Check the response
    assert response.status_code == 401


def test_get_memories_insufficient_scope(test_client, test_user, db_session):
    """Test getting memories with insufficient scope."""
    # Create a test client for the user with limited scope
    from app.models.oauth import OAuthClient
    client = OAuthClient(
        client_name="Limited Scope Client",
        client_id=uuid.uuid4(),
        client_secret="test_secret",
        redirect_uris=["http://localhost:8000/callback"],
        scopes=["memories:write"]  # Missing memories:read
    )
    db_session.add(client)
    db_session.commit()
    
    # Create an access token with limited scope
    token, _, _ = create_access_token(
        db=db_session,
        client_id=client.client_id,
        user_id=test_user.id,
        scope="memories:write"  # Missing memories:read
    )
    
    # Make the request
    response = test_client.get(
        "/api/memories/",
        headers={
            "Authorization": f"Bearer {token}"
            # Removed X-Test-Override-Scopes to test actual scope checking
        }
    )
    
    # Check the response
    assert response.status_code == 403
    data = response.json()
    assert "error" in data["detail"]
    assert data["detail"]["error"] == "insufficient_scope"


def test_create_memory(test_client, test_token, db_session, test_user):
    """Test creating a memory."""
    # Prepare the request data
    memory_data = {
        "memory_content": "New test memory",
        "permission": "public",
        "expiration_date": (datetime.utcnow() + timedelta(days=1)).isoformat()
    }
    
    # Make the request
    response = test_client.post(
        "/api/memories/",
        headers={
            "Authorization": f"Bearer {test_token}",
            "X-Test-Override-Scopes": "true"
        },
        json=memory_data
    )
    
    # Check the response
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "text" in data
    assert "permission" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "expiration_date" in data
    assert data["text"] == "New test memory"
    assert data["permission"] == "public"
    
    # Check that the memory was created in the database
    memory_id = uuid.UUID(data["id"])
    db_session.commit()  # Ensure any pending transactions are committed
    db_session.expire_all()  # Clear the session cache
    memory = db_session.query(Memory).filter(Memory.id == memory_id).first()
    assert memory is not None
    assert memory.text == "New test memory"
    assert memory.permission == "public"
    assert memory.user_id == test_user.id


def test_create_memory_unauthorized(test_client):
    """Test creating a memory without authorization."""
    # Prepare the request data
    memory_data = {
        "memory_content": "New test memory",
        "permission": "public"
    }
    
    # Make the request without a token
    response = test_client.post(
        "/api/memories/",
        json=memory_data
    )
    
    # Check the response
    assert response.status_code == 401


def test_create_memory_insufficient_scope(test_client, test_user, db_session):
    """Test creating a memory with insufficient scope."""
    # Create a test client for the user with limited scope
    from app.models.oauth import OAuthClient
    client = OAuthClient(
        client_name="Limited Scope Client",
        client_id=uuid.uuid4(),
        client_secret="test_secret",
        redirect_uris=["http://localhost:8000/callback"],
        scopes=["memories:read"]  # Missing memories:write
    )
    db_session.add(client)
    db_session.commit()
    
    # Create an access token with limited scope
    token, _, _ = create_access_token(
        db=db_session,
        client_id=client.client_id,
        user_id=test_user.id,
        scope="memories:read"  # Missing memories:write
    )
    
    # Prepare the request data
    memory_data = {
        "memory_content": "New test memory",
        "permission": "public"
    }
    
    # Make the request
    response = test_client.post(
        "/api/memories/",
        headers={
            "Authorization": f"Bearer {token}"
            # Removed X-Test-Override-Scopes to test actual scope checking
        },
        json=memory_data
    )
    
    # Check the response
    assert response.status_code == 403
    data = response.json()
    assert "error" in data["detail"]
    assert data["detail"]["error"] == "insufficient_scope"


def test_update_memory(test_client, test_token, test_memory, db_session):
    """Test updating a memory."""
    # Make sure the memory exists in the database
    db_session.refresh(test_memory)
    
    # Print the memory ID for debugging
    print(f"Updating memory with ID: {test_memory.id}")
    
    # Prepare the request data
    memory_update = {
        "text": "Updated memory content",
        "permission": "public",
        "expiration_date": (datetime.utcnow() + timedelta(days=2)).isoformat()
    }
    
    # Make the request
    response = test_client.put(
        f"/api/memories/{test_memory.id}",
        headers={
            "Authorization": f"Bearer {test_token}",
            "X-Test-Override-Scopes": "true"
        },
        json=memory_update
    )
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "text" in data
    assert "permission" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "expiration_date" in data
    assert data["text"] == "Updated memory content"
    assert data["permission"] == "public"
    
    # Check that the memory was updated in the database
    db_session.refresh(test_memory)
    assert test_memory.text == "Updated memory content"
    assert test_memory.permission == "public"


def test_update_memory_not_found(test_client, test_token):
    """Test updating a non-existent memory."""
    # Prepare the request data
    memory_update = {
        "text": "Updated memory content",
        "permission": "public"
    }
    
    # Make the request with a non-existent memory ID
    response = test_client.put(
        f"/api/memories/{uuid.uuid4()}",
        headers={
            "Authorization": f"Bearer {test_token}",
            "X-Test-Override-Scopes": "true"
        },
        json=memory_update
    )
    
    # Check the response
    assert response.status_code == 404
    data = response.json()
    assert "error" in data["detail"]
    assert data["detail"]["error"] == "Memory not found"


def test_delete_memory(test_client, test_token, test_memory, db_session):
    """Test deleting a memory."""
    # Make sure the memory exists in the database
    db_session.refresh(test_memory)
    
    # Print the memory ID for debugging
    print(f"Deleting memory with ID: {test_memory.id}")
    
    # Make the request
    response = test_client.delete(
        f"/api/memories/{test_memory.id}",
        headers={
            "Authorization": f"Bearer {test_token}",
            "X-Test-Override-Scopes": "true"
        }
    )
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert f"Memory {test_memory.id} deleted successfully" in data["message"]
    
    # Check that the memory was deleted from the database
    memory = db_session.query(Memory).filter(Memory.id == test_memory.id).first()
    assert memory is None


def test_delete_memory_not_found(test_client, test_token):
    """Test deleting a non-existent memory."""
    # Make the request with a non-existent memory ID
    response = test_client.delete(
        f"/api/memories/{uuid.uuid4()}",
        headers={
            "Authorization": f"Bearer {test_token}",
            "X-Test-Override-Scopes": "true"
        }
    )
    
    # Check the response
    assert response.status_code == 404
    data = response.json()
    assert "error" in data["detail"]
    assert data["detail"]["error"] == "Memory not found"
