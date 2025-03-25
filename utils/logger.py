#!/usr/bin/env python3
# Logger - Setup logging configuration for the Agentic Form Filler

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logger(log_level=logging.INFO, log_to_file=True) -> logging.Logger:
    """
    Set up and configure the application logger.
    
    Args:
        log_level: Logging level (default: INFO)
        log_to_file: Whether to log to file in addition to console
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    if log_to_file:
        os.makedirs('logs', exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if enabled)
    if log_to_file:
        # Create a timestamp for the log filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = f"logs/form_filler_{timestamp}.log"
        
        # Create rotating file handler (max 10MB, keep 5 backups)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"Log file created at: {log_file}")
    
    logger.info("Logger initialized")
    return logger 