from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

@dataclass
class AppContext:
    """Application context for MCP server"""
    db: AsyncSession

from app.models.memory import Memory
from app.models.user import User
from app.models.oauth import OAuthClient, OAuthToken
