"""
Logger configuration for the MCP server.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
import json

def setup_logger(name: str = "mcp_server", log_level: str = "INFO") -> logging.Logger:
    """
    Set up and configure logger
    
    Args:
        name: Name of the logger
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    # Convert string log level to logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers if any
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Define log format
    log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Set up console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # Set up file handler with rotation
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, f"{name}.log"),
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger

def get_json_logger(name: str = "mcp_server", log_level: str = "INFO") -> logging.Logger:
    """
    Get a JSON-formatted logger for structured logging in production.
    
    This is a wrapper around the JSON logger from json_logger.py
    
    Args:
        name: Name of the logger
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        JSON-formatted logger instance
    """
    from app.utils.json_logger import setup_json_logger
    return setup_json_logger(name, log_level)

# Determine if we should use JSON logging based on environment
use_json = os.getenv("USE_JSON_LOGGING", "false").lower() == "true"

# Create default logger based on environment
logger = get_json_logger() if use_json else setup_logger()
