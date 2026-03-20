"""
Shared logging factory for the trading analysis app.
All modules should import get_logger from here for consistent formatting.
"""
import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """Return a consistently formatted logger for the given module name."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
