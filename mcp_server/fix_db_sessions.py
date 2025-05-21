#!/usr/bin/env python3
"""
Script to fix database session handling in the MCP server.
This script updates all the necessary files to use the new db_utils.get_session_from_generator function.
"""
import os
import re
import glob

# Define the pattern to search for
OLD_PATTERN = r"# Get the database session from the generator\s+db = await anext\(db_gen\)"
NEW_REPLACEMENT = "# Get the database session from the generator\ndb = await get_session_from_generator(db_gen)"

# Define the import statement to add
IMPORT_STATEMENT = "from app.utils.db_utils import get_session_from_generator"

def add_import_if_needed(file_path, import_statement):
    """Add import statement if it's not already in the file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    if import_statement not in content:
        # Find the last import statement
        import_lines = re.findall(r'^import.*$|^from.*import.*$', content, re.MULTILINE)
        if import_lines:
            last_import = import_lines[-1]
            # Insert our import after the last import
            content = content.replace(last_import, f"{last_import}\n{import_statement}")
        else:
            # If no imports found, add at the beginning
            content = f"{import_statement}\n\n{content}"
        
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Added import to {file_path}")

def replace_db_session_code(file_path, old_pattern, new_replacement):
    """Replace the old database session code with the new one."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace the pattern
    new_content = re.sub(old_pattern, new_replacement, content)
    
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Updated database session handling in {file_path}")
        return True
    return False

def main():
    # Create the db_utils.py file if it doesn't exist
    db_utils_dir = os.path.join('app', 'utils')
    os.makedirs(db_utils_dir, exist_ok=True)
    
    db_utils_path = os.path.join(db_utils_dir, 'db_utils.py')
    if not os.path.exists(db_utils_path):
        db_utils_content = '''"""
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
'''
        with open(db_utils_path, 'w') as f:
            f.write(db_utils_content)
        print(f"Created {db_utils_path}")
    
    # Find all Python files in the app directory
    python_files = glob.glob('app/**/*.py', recursive=True)
    
    # Process each file
    for file_path in python_files:
        # Skip the db_utils.py file itself
        if file_path == db_utils_path:
            continue
        
        # Check if the file contains database session code
        with open(file_path, 'r') as f:
            content = f.read()
        
        if "db_gen = Depends(get_db)" in content:
            # Add the import statement if needed
            add_import_if_needed(file_path, IMPORT_STATEMENT)
            
            # Replace the database session code
            replaced = replace_db_session_code(file_path, OLD_PATTERN, NEW_REPLACEMENT)
            if replaced:
                print(f"Updated {file_path}")

if __name__ == "__main__":
    main()
