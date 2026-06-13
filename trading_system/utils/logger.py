"""
Logging configuration.
"""

import logging
import sys
from datetime import datetime
import os


def get_logger(name: str) -> logging.Logger:
    """
    Get or create logger.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    # Only configure root logger once
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        os.makedirs('./logs', exist_ok=True)
        file_handler = logging.FileHandler(
            f'./logs/trading_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger
