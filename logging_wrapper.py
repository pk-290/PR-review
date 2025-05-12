import functools
import logging
import traceback
from datetime import datetime
from typing import Callable, Any, Optional, Dict, Tuple, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pr_reviewer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("pr_reviewer")

def log_exceptions(func):
    """Decorator to log exceptions for synchronous functions"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        func_name = func.__name__
        try:
            logger.info(f"Starting {func_name}")
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Completed {func_name} in {execution_time}s")
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error in {func_name} after {execution_time}s: {str(e)}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise
    return wrapper

def log_async_exceptions(func):
    """Decorator to log exceptions for async functions"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = datetime.now()
        func_name = func.__name__
        try:
            logger.info(f"Starting async {func_name}")
            result = await func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Completed async {func_name} in {execution_time}s")
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error in async {func_name} after {execution_time}s: {str(e)}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise
    return wrapper