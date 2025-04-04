import logging
import os
from logging.handlers import RotatingFileHandler

"""TODO:
Better way of importing/using this."""

LOGGER = None

class LevelFilter(logging.Filter):
    def __init__(self, excluded_levels):
        self.excluded_levels = excluded_levels

    def filter(self, record):
        return record.levelno not in self.excluded_levels

class AppLogger:
    def __init__(self, name="app", log_dir="logs", max_log_size=5*1024*1024, ignore_levels=None):
        """
        Args:
            ignore_levels: List of levels to ignore (e.g., [logging.DEBUG, logging.WARNING])
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)  # Default level (can be overridden)
        
        os.makedirs(log_dir, exist_ok=True)
        log_file = f"{log_dir}/{name}.log"
        
        handler = RotatingFileHandler(
            log_file, maxBytes=max_log_size, backupCount=3
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add filter to ignore specified levels
        if ignore_levels:
            handler.addFilter(LevelFilter(excluded_levels=ignore_levels))
        
        self.logger.addHandler(handler)
    
    def get_logger(self):
        return self.logger
    



