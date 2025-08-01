"""
Logging configuration for MUFI application
"""
import logging
import sys
from typing import Optional


def setup_logging(
    level: str = "INFO",
    format_str: Optional[str] = None
) -> None:
    """
    Setup application logging configuration
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_str: Custom format string for log messages
    """
    if format_str is None:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_str,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Application logger
logger = get_logger(__name__) 