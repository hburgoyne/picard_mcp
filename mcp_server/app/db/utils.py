from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

async def check_database_connection(db: AsyncSession) -> bool:
    """
    Check if the database connection is working.
    
    Args:
        db: AsyncSession: The database session
        
    Returns:
        bool: True if the connection is working, False otherwise
    """
    try:
        # Execute a simple query to check the connection
        result = await db.execute(text("SELECT 1"))
        return result.scalar() == 1
    except Exception:
        return False

async def initialize_db(db: AsyncSession) -> None:
    """
    Initialize the database with any required setup.
    
    Args:
        db: AsyncSession: The database session
    """
    # Check if pgvector extension is installed
    try:
        await db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise Exception(f"Failed to initialize pgvector extension: {e}")
