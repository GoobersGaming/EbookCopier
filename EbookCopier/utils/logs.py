import os
import sys
import logging
from logging.handlers import RotatingFileHandler
logger = logging.getLogger(__name__)



class LevelFilter(logging.Filter):
    """Create filter for logger"""
    def __init__(self, excluded_levels):
        self.excluded_levels = excluded_levels

def setup_logging(log_dir="logs", max_log_size=5*1024*1024, ignore_levels=None, console_logging=False, console_level=logging.INFO):
    """Setups up a logger and console logger"""
    os.makedirs(log_dir, exist_ok=True)
    log_file = f"{log_dir}/Ebook.log"

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # RotatingFileHandler
    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_log_size, backupCount=3
    )
    file_handler.setFormatter(formatter)

    if ignore_levels:
        file_handler.addFilter(LevelFilter(excluded_levels=ignore_levels))
    
    #Console Handler
    if console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(console_level)
    
    # apply configuration to root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    #prevent duplicates
    root_logger.handlers.clear()

    # add handlers
    root_logger.addHandler(file_handler)
    if console_logging:
        root_logger.addHandler(console_handler)
    
    return root_logger



