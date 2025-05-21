"""
Configuration file for pytest.

This file contains fixtures that are available to all tests.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import Base, get_db
from app.core.config import settings

# Create a test database URL with a unique test database name
TEST_DATABASE_URL = settings.DATABASE_URL.replace(settings.POSTGRES_DB, f"{settings.POSTGRES_DB}_test")

# Create the test engine
test_engine = create_engine(TEST_DATABASE_URL)

# Create the pgvector extension in the test database if it doesn't exist
def create_pgvector_extension():
    """Create the pgvector extension in the test database."""
    conn = test_engine.connect()
    try:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    finally:
        conn.close()

# Create the test SessionLocal
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="module")
def test_app():
    """Return a TestClient instance for testing the app."""
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database for each test.
    
    This fixture creates all tables in a test database, yields a
    session for tests to use, and cleans up after the test is done.
    """
    # Create pgvector extension
    create_pgvector_extension()
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create a new session
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        
    # Drop all tables after the test is done
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def override_get_db(db_session):
    """
    Override the get_db dependency to use the test session.
    """
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()
