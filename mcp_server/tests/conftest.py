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
from sqlalchemy import text

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  

# Import app
from app.main import app
from app.core.config import settings
from app.db.session import get_db, Base

# Create a test database URL
TEST_DATABASE_URL = settings.ASYNC_DATABASE_URL + "_test"

# Extract the database name from the URL
db_name = TEST_DATABASE_URL.split("/")[-1]

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
    # Create the test database if it doesn't exist
    # Connect to the default postgres database to create the test database
    default_engine = create_async_engine(
        settings.ASYNC_DATABASE_URL.rsplit('/', 1)[0] + '/postgres',
        poolclass=NullPool,
        isolation_level='AUTOCOMMIT'
    )
    
    try:
        async with default_engine.begin() as conn:
            # Check if database exists
            result = await conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
            if result.scalar() is None:
                print(f"Creating test database: {db_name}")
                await conn.execute(text(f"CREATE DATABASE {db_name}"))
    except Exception as e:
        print(f"Error creating test database: {e}")
    finally:
        await default_engine.dispose()
    
    # Now connect to the test database and create tables
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
        # Initialize pgvector extension
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception as e:
            print(f"Error initializing pgvector extension: {e}")
    
    yield
    
    # Drop the test database after all tests are done
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(setup_test_db):
    """Return a database session for each test."""
    async with TestingSessionLocal() as session:
        yield session

# This is a key change - we're completely replacing the get_db dependency
# with a simple function that returns the test session directly
@pytest.fixture
def override_get_db(db_session):
    """Override the get_db dependency for testing."""
    async def _get_test_db():
        yield db_session
    
    return _get_test_db

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
