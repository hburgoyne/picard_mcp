"""
JSON logging formatters for more structured logging output.
"""
import json
import logging
import traceback
from datetime import datetime
import socket
import os

class JSONFormatter(logging.Formatter):
    """
    Format logs as JSON for easier parsing by log management systems.
    """
    def __init__(self, **kwargs):
        super().__init__()
        self.hostname = socket.gethostname()
        self.json_default = kwargs.get("json_default", str)

    def format(self, record):
        """
        Format the log record as JSON.
        """
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "filename": record.filename,
            "lineno": record.lineno,
            "funcName": record.funcName,
            "process": record.process,
            "processName": record.processName,
            "thread": record.thread,
            "threadName": record.threadName,
            "hostname": self.hostname,
            "service": "mcp_server"
        }
        
        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key.startswith('_') or key in log_data:
                continue
            log_data[key] = value
            
        return json.dumps(log_data, default=self.json_default)

def setup_json_logger(name="mcp_server", log_level="INFO"):
    """
    Set up a logger with JSON formatting for production environments.
    
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
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create a JSON formatter
    json_formatter = JSONFormatter()
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)
    
    # Set up file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(logs_dir, f"{name}.json.log"),
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger
