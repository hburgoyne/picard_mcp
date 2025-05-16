import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings

# Create async database URL
ASYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create engine and session
engine = create_async_engine(ASYNC_DATABASE_URL, poolclass=NullPool)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Create base model
Base = declarative_base()

async def init_db():
    """Initialize database connection"""
    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    db = SessionLocal()
    return db

async def close_db(db: AsyncSession):
    """Close database connection"""
    await db.close()

async def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()
