"""Tests for the MCP tools endpoints."""
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
    """Create a test user for tools tests."""
    # First check if the test user already exists
    user = db_session.query(User).filter(User.username == "testuser").first()
    if user:
        return user
        
    # Create a test user with a fixed ID to match what auth.py will use
    user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
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
    
    # Check if a test memory already exists for this user
    existing_memory = db_session.query(Memory).filter(Memory.user_id == test_user.id).first()
    if existing_memory:
        return existing_memory
    
    memory = Memory(
        user_id=test_user.id,
        text="This is a test memory",
        permission="private"
    )
    db_session.add(memory)
    db_session.commit()
    db_session.refresh(memory)  # Make sure we have the latest data
    return memory


def test_submit_memory(test_client, test_token, db_session, test_user):
    """Test submitting a memory using the tools endpoint."""
    # Prepare the request data
    memory_data = {
        "tool": "submit_memory",
        "data": {
            "text": "New test memory from tools",
            "permission": "public",
            "expiration_date": (datetime.utcnow() + timedelta(days=1)).isoformat()
        }
    }
    
    # Make the request
    response = test_client.post(
        "/api/tools/",
        headers={"Authorization": f"Bearer {test_token}", "X-Test-Override-Scopes": "true"},
        json=memory_data
    )
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "id" in data["data"]
    assert "text" in data["data"]
    assert "permission" in data["data"]
    assert "created_at" in data["data"]
    assert "updated_at" in data["data"]
    assert "expiration_date" in data["data"]
    assert data["data"]["text"] == "New test memory from tools"
    assert data["data"]["permission"] == "public"
    
    # Check that the memory was created in the database
    memory_id = uuid.UUID(data["data"]["id"])
    memory = db_session.query(Memory).filter(Memory.id == memory_id).first()
    assert memory is not None
    assert memory.text == "New test memory from tools"
    assert memory.permission == "public"
    assert memory.user_id == test_user.id


def test_retrieve_memories(test_client, test_token, test_memory):
    """Test retrieving memories using the tools endpoint."""
    # Prepare the request data
    request_data = {
        "tool": "retrieve_memories",
        "data": {}
    }
    
    # Make the request
    response = test_client.post(
        "/api/tools/",
        headers={"Authorization": f"Bearer {test_token}", "X-Test-Override-Scopes": "true"},
        json=request_data
    )
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "memories" in data["data"]
    assert len(data["data"]["memories"]) > 0
    
    # Check the memory data
    memory = data["data"]["memories"][0]
    assert "id" in memory
    assert "text" in memory
    assert "permission" in memory
    assert "created_at" in memory
    assert "updated_at" in memory
    assert memory["text"] == "This is a test memory"
    assert memory["permission"] == "private"


def test_update_memory(test_client, test_token, test_memory, db_session):
    """Test updating a memory using the tools endpoint."""
    # Prepare the request data
    memory_data = {
        "tool": "update_memory",
        "data": {
            "memory_id": str(test_memory.id),
            "text": "Updated memory content from tools",
            "permission": "public",
            "expiration_date": (datetime.utcnow() + timedelta(days=2)).isoformat()
        }
    }
    
    # Make the request
    response = test_client.post(
        "/api/tools/",
        headers={"Authorization": f"Bearer {test_token}", "X-Test-Override-Scopes": "true"},
        json=memory_data
    )
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "id" in data["data"]
    assert "text" in data["data"]
    assert "permission" in data["data"]
    assert "created_at" in data["data"]
    assert "updated_at" in data["data"]
    assert "expiration_date" in data["data"]
    assert data["data"]["text"] == "Updated memory content from tools"
    assert data["data"]["permission"] == "public"
    
    # Check that the memory was updated in the database
    db_session.refresh(test_memory)
    assert test_memory.text == "Updated memory content from tools"
    assert test_memory.permission == "public"


def test_delete_memory(test_client, test_token, test_memory, db_session):
    """Test deleting a memory using the tools endpoint."""
    # Prepare the request data
    memory_data = {
        "tool": "delete_memory",
        "data": {
            "memory_id": str(test_memory.id)
        }
    }
    
    # Make the request
    response = test_client.post(
        "/api/tools/",
        headers={"Authorization": f"Bearer {test_token}", "X-Test-Override-Scopes": "true"},
        json=memory_data
    )
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "message" in data["data"]
    assert f"Memory {test_memory.id} deleted successfully" in data["data"]["message"]
    
    # Check that the memory was deleted from the database
    memory = db_session.query(Memory).filter(Memory.id == test_memory.id).first()
    assert memory is None


def test_modify_permissions(test_client, test_token, test_memory, db_session):
    """Test modifying memory permissions using the tools endpoint."""
    # Prepare the request data
    memory_data = {
        "tool": "modify_permissions",
        "data": {
            "memory_id": str(test_memory.id),
            "permission": "public"
        }
    }
    
    # Make the request
    response = test_client.post(
        "/api/tools/",
        headers={"Authorization": f"Bearer {test_token}", "X-Test-Override-Scopes": "true"},
        json=memory_data
    )
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "id" in data["data"]
    assert "permission" in data["data"]
    assert data["data"]["permission"] == "public"
    
    # Check that the memory permission was updated in the database
    db_session.refresh(test_memory)
    assert test_memory.permission == "public"


def test_unknown_tool(test_client, test_token):
    """Test using an unknown tool."""
    # Prepare the request data
    request_data = {
        "tool": "unknown_tool",
        "data": {}
    }
    
    # Make the request
    response = test_client.post(
        "/api/tools/",
        headers={"Authorization": f"Bearer {test_token}", "X-Test-Override-Scopes": "true"},
        json=request_data
    )
    
    # Check the response
    assert response.status_code == 400
    data = response.json()
    assert "error" in data["detail"]
    assert "Unknown tool" in data["detail"]["error"]
