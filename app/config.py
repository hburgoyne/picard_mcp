import os
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # PostgreSQL Configuration
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_DB: str = Field(default="picard_mcp")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    
    # Database URL
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # MCP Server Configuration
    MCP_SERVER_NAME: str = Field(default="Picard MCP")
    MCP_SERVER_HOST: str = Field(default="0.0.0.0")
    MCP_SERVER_PORT: int = Field(default=8000)
    MCP_ISSUER_URL: str = Field(default="http://localhost:8000")
    
    # OAuth Configuration
    OAUTH_CLIENT_ID: str = Field(default="picard_client")
    OAUTH_CLIENT_SECRET: str = Field(default="picard_secret")
    OAUTH_REDIRECT_URI: str = Field(default="http://localhost:8000/oauth/callback")
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(default="")
    
    # LangChain Configuration
    LANGCHAIN_TRACING_V2: bool = Field(default=False)
    LANGCHAIN_ENDPOINT: str = Field(default="https://api.smith.langchain.com")
    LANGCHAIN_API_KEY: str = Field(default="")
    LANGCHAIN_PROJECT: str = Field(default="picard_mcp")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = Field(default="supersecret")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    
    # Render Configuration
    RENDER_EXTERNAL_URL: str = Field(default="https://your-app-name.onrender.com")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields to prevent validation errors

# Create settings instance
settings = Settings()
