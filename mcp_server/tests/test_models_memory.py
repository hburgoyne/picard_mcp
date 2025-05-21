"""Tests for the Memory model."""
import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import inspect
from app.models.memory import Memory
from app.models.user import User


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
    return user


def test_memory_creation(db_session, test_user):
    """Test that a memory can be created."""
    memory = Memory(
        user_id=test_user.id,
        text="This is a test memory",
        permission="private"
    )
    db_session.add(memory)
    db_session.commit()
    
    # Query the memory
    db_memory = db_session.query(Memory).filter(Memory.text == "This is a test memory").first()
    
    assert db_memory is not None
    assert db_memory.text == "This is a test memory"
    assert db_memory.user_id == test_user.id
    assert db_memory.permission == "private"
    assert db_memory.encrypted_text is None
    assert db_memory.embedding is None
    assert db_memory.expiration_date is None
    assert isinstance(db_memory.id, uuid.UUID)
    assert db_memory.created_at is not None
    assert db_memory.updated_at is not None


def test_memory_with_expiration(db_session, test_user):
    """Test memory with expiration date."""
    # Create memory that expires tomorrow
    tomorrow = datetime.utcnow() + timedelta(days=1)
    future_memory = Memory(
        user_id=test_user.id,
        text="This memory expires tomorrow",
        permission="private",
        expiration_date=tomorrow
    )
    db_session.add(future_memory)
    db_session.commit()
    
    # Create memory that expired yesterday
    yesterday = datetime.utcnow() - timedelta(days=1)
    past_memory = Memory(
        user_id=test_user.id,
        text="This memory expired yesterday",
        permission="private",
        expiration_date=yesterday
    )
    db_session.add(past_memory)
    db_session.commit()
    
    # Test is_expired property
    assert future_memory.is_expired is False
    assert past_memory.is_expired is True


def test_memory_with_embedding(db_session, test_user):
    """Test memory with embedding vector."""
    # Create a simple 1536-dimension vector for testing
    test_embedding = [0.0] * 1536
    
    memory = Memory(
        user_id=test_user.id,
        text="This is a memory with embedding",
        permission="private",
        embedding=test_embedding
    )
    db_session.add(memory)
    db_session.commit()
    
    # Query the memory
    db_memory = db_session.query(Memory).filter(
        Memory.text == "This is a memory with embedding"
    ).first()
    
    # Check that the embedding was saved
    assert db_memory is not None
    assert db_memory.embedding is not None
    assert len(db_memory.embedding) == 1536


def test_user_memory_relationship(db_session, test_user):
    """Test the relationship between User and Memory models."""
    # Create several memories for the user
    memory1 = Memory(
        user_id=test_user.id,
        text="Memory 1",
        permission="private"
    )
    memory2 = Memory(
        user_id=test_user.id,
        text="Memory 2",
        permission="public"
    )
    db_session.add_all([memory1, memory2])
    db_session.commit()
    
    # Refresh the user object to update relationships
    db_session.refresh(test_user)
    
    # Test that the user has the memories
    assert len(test_user.memories) == 2
    assert any(m.text == "Memory 1" for m in test_user.memories)
    assert any(m.text == "Memory 2" for m in test_user.memories)
    
    # Test the back-reference from memory to user
    for memory in test_user.memories:
        assert memory.user.id == test_user.id
