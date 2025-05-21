"""
Database utility functions for handling async sessions.
"""
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

async def get_session_from_generator(db_gen):
    """
    Extract a database session from either an async generator or a direct session.
    
    This handles both production and test environments:
    - In production, db_gen is an async generator from get_db()
    - In tests, db_gen might be a direct AsyncSession object
    
    Args:
        db_gen: Either an async generator or an AsyncSession
        
    Returns:
        AsyncSession: The database session
    """
    if hasattr(db_gen, 'execute') and callable(getattr(db_gen, 'execute')):
        # It's already a session (likely in test environment)
        logger.debug("Using direct database session")
        return db_gen
    else:
        # It's an async generator (in normal environment)
        try:
            logger.debug("Extracting session from async generator")
            session = await anext(db_gen)
            return session
        except Exception as e:
            logger.error(f"Error extracting session from generator: {e}")
            raise
