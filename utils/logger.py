"""
Logger module for the Trading Information Scraper application.

This module provides functionality for setting up and configuring the logging system.
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Dict, Optional, Union


def setup_logger(
    name: str = None,
    level: Union[int, str] = logging.INFO,
    log_file: Optional[str] = None,
    log_to_console: bool = True,
    log_format: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    rotate_when: str = 'midnight',
    use_rotating_file: bool = True
) -> logging.Logger:
    """
    Set up and configure a logger.
    
    Args:
        name: Logger name (if None, use the root logger)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to the log file (if None, log only to console)
        log_to_console: Whether to log to the console
        log_format: Log message format (if None, use a default format)
        max_bytes: Maximum log file size in bytes (for RotatingFileHandler)
        backup_count: Number of backup log files to keep
        rotate_when: When to rotate log files (for TimedRotatingFileHandler)
        use_rotating_file: Whether to use RotatingFileHandler (True) or TimedRotatingFileHandler (False)
        
    Returns:
        Configured logger
    """
    # Get the logger
    logger = logging.getLogger(name)
    
    # Clear any existing handlers
    logger.handlers = []
    
    # Set the logging level
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    logger.setLevel(level)
    
    # Set the log format
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    
    # Add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if a log file is specified
    if log_file:
        # Create the directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Create the file handler
        if use_rotating_file:
            # Use RotatingFileHandler for size-based rotation
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
        else:
            # Use TimedRotatingFileHandler for time-based rotation
            file_handler = TimedRotatingFileHandler(
                log_file,
                when=rotate_when,
                backupCount=backup_count
            )
        
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to the root logger
    logger.propagate = False
    
    return logger


def get_log_levels() -> Dict[str, int]:
    """
    Get a dictionary of available log levels.
    
    Returns:
        Dictionary mapping level names to their numeric values
    """
    return {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }


def log_exception(logger: logging.Logger, exc: Exception, context: Optional[str] = None) -> None:
    """
    Log an exception with context information.
    
    Args:
        logger: Logger to use
        exc: Exception to log
        context: Additional context information
    """
    if context:
        logger.error(f"{context}: {exc}", exc_info=True)
    else:
        logger.error(f"Exception: {exc}", exc_info=True)


def create_timed_logger(
    name: str,
    log_dir: str = './logs',
    level: Union[int, str] = logging.INFO
) -> logging.Logger:
    """
    Create a logger that logs to a file with the current date in the filename.
    
    Args:
        name: Logger name
        log_dir: Directory to store log files
        level: Logging level
        
    Returns:
        Configured logger
    """
    # Create the log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate a filename with the current date
    date_str = datetime.now().strftime('%Y%m%d')
    log_file = os.path.join(log_dir, f"{name}_{date_str}.log")
    
    # Set up the logger
    return setup_logger(
        name=name,
        level=level,
        log_file=log_file,
        log_to_console=True
    )


def configure_logging_from_config(config: Dict) -> Dict[str, logging.Logger]:
    """
    Configure logging based on configuration settings.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary of configured loggers
    """
    loggers = {}
    
    # Configure the root logger
    root_config = config.get('logging', {})
    root_level = root_config.get('level', 'INFO')
    root_file = root_config.get('file', './logs/app.log')
    
    loggers['root'] = setup_logger(
        name=None,
        level=root_level,
        log_file=root_file,
        log_to_console=True
    )
    
    # Configure additional loggers if specified
    additional_loggers = root_config.get('loggers', {})
    for name, logger_config in additional_loggers.items():
        level = logger_config.get('level', root_level)
        log_file = logger_config.get('file', None)
        
        loggers[name] = setup_logger(
            name=name,
            level=level,
            log_file=log_file,
            log_to_console=logger_config.get('console', True)
        )
    
    return loggers