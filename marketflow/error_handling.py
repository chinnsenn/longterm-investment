"""Common error handling utilities for the MarketFlow application."""
import logging
import functools
import time
from typing import Callable, Any, TypeVar, ParamSpec
from .constants import DEFAULT_ERROR_RETRY_COUNT, RETRY_INTERVAL

P = ParamSpec('P')
T = TypeVar('T')


def handle_database_errors(func: Callable[P, T]) -> Callable[P, T]:
    """Decorator for handling database errors consistently."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Database error in {func.__name__}: {str(e)}")
            raise  # Re-raise after logging
    
    return wrapper


def handle_market_data_errors(func: Callable[P, T]) -> Callable[P, T]:
    """Decorator for handling market data API errors consistently."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Market data error in {func.__name__}: {str(e)}")
            raise  # Re-raise after logging
    
    return wrapper


def retry_on_failure(max_retries: int = DEFAULT_ERROR_RETRY_COUNT, 
                     delay: float = RETRY_INTERVAL,
                     allowed_exceptions: tuple = (Exception,)):
    """
    Decorator to retry a function on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        allowed_exceptions: Tuple of exceptions to retry on
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except allowed_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logging.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}")
                        logging.info(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        logging.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
            
            raise last_exception
        
        return wrapper
    return decorator


def setup_logging_with_format(level: int = logging.INFO):
    """Setup logging with consistent formatting."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('investment.log')
        ]
    )


class MarketFlowLogger:
    """Centralized logger for the MarketFlow application."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, **kwargs)