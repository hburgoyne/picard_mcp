import pytest
import os
import sys
import asyncio
from fastapi.testclient import TestClient
from jose import jwt
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  

# Import app
from app.main import app
from app.core.config import settings
from app.db.session import get_db, Base

# Create a test database URL
TEST_DATABASE_URL = settings.ASYNC_DATABASE_URL + "_test"

# Create a test engine
engine_test = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

# Create a test session factory
TestingSessionLocal = sessionmaker(
    engine_test,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def setup_test_db():
    """Set up the test database once per session."""
    # Create the test database and tables
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Drop the test database after all tests are done
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(setup_test_db):
    """Return a database session for each test."""
    connection = await engine_test.connect()
    transaction = await connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()

@pytest.fixture
def override_get_db(db_session):
    """Override the get_db dependency for testing."""
    # Create a simple dependency that yields the session
    async def _override_get_db():
        yield db_session
    return _override_get_db

@pytest.fixture
def test_app(override_get_db):
    """Return the FastAPI app for testing with overridden dependencies."""
    # Override the get_db dependency
    app.dependency_overrides[get_db] = override_get_db
    yield app
    # Clear the overrides after the test
    app.dependency_overrides = {}

@pytest.fixture
def client(test_app):
    """Return a TestClient for the FastAPI app."""
    with TestClient(test_app) as client:
        yield client

@pytest.fixture
def auth_headers():
    """Return authentication headers for testing."""
    # Create a simple JWT token for testing
    payload = {
        "sub": "1",
        "scopes": ["memories:read", "memories:write", "profile:read"],
        "exp": datetime.utcnow() + timedelta(minutes=60),
        "iat": datetime.utcnow(),
        "jti": str(os.urandom(16).hex())
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return {"Authorization": f"Bearer {token}"}
