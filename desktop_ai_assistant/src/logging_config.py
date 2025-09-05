"""
Logging configuration for the SAGE Desktop AI Assistant.
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from config.settings import LOGGING_CONFIG

def setup_logging():
    """Configure logging for the application."""
    
    # Create logs directory if it doesn't exist
    log_file = Path(LOGGING_CONFIG["file"])
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(LOGGING_CONFIG["format"])
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOGGING_CONFIG["level"]))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=LOGGING_CONFIG["max_bytes"],
        backupCount=LOGGING_CONFIG["backup_count"]
    )
    file_handler.setLevel(getattr(logging, LOGGING_CONFIG["level"]))
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Set third-party loggers to WARNING level to reduce noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("pygame").setLevel(logging.WARNING)
    
    logging.info("Logging configured successfully")
