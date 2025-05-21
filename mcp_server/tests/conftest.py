import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
import sys
from typing import Generator, AsyncGenerator

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.db.session import Base, get_db
from app.models.user import User
from app.utils.security import get_password_hash

# Test database URL for Docker environment
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db-mcp:5432/test_picard_mcp"

# Create async test engine
test_engine = create_async_engine(TEST_DATABASE_URL)
TestingAsyncSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def setup_database():
    """Set up the test database once for all tests."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create test data
    async with TestingAsyncSessionLocal() as session:
        # Create test user
        test_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpassword"),
            full_name="Test User"
        )
        session.add(test_user)
        await session.commit()
    
    yield
    
    # Clean up
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Get a test database session for each test."""
    async with TestingAsyncSessionLocal() as session:
        yield session

@pytest.fixture
async def client(db_session) -> Generator:
    """Get a test client with a test database session."""
    async def override_get_db():
        try:
            yield db_session
        finally:
            await db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
