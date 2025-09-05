"""
Error handling and exception management utilities.
"""
import logging
import traceback
import functools
from typing import Any, Callable, Optional, Type
import asyncio

logger = logging.getLogger(__name__)


def handle_exceptions(
    default_return: Any = None,
    log_errors: bool = True,
    reraise: bool = False,
    exception_types: tuple = (Exception,)
):
    """
    Decorator for handling exceptions in functions.
    
    Args:
        default_return: Value to return if exception occurs
        log_errors: Whether to log exceptions
        reraise: Whether to reraise the exception after logging
        exception_types: Tuple of exception types to catch
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                if log_errors:
                    logger.error(
                        f"Exception in {func.__name__}: {e}",
                        exc_info=True
                    )
                if reraise:
                    raise
                return default_return
        return wrapper
    return decorator


def handle_async_exceptions(
    default_return: Any = None,
    log_errors: bool = True,
    reraise: bool = False,
    exception_types: tuple = (Exception,)
):
    """
    Decorator for handling exceptions in async functions.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except exception_types as e:
                if log_errors:
                    logger.error(
                        f"Exception in {func.__name__}: {e}",
                        exc_info=True
                    )
                if reraise:
                    raise
                return default_return
        return wrapper
    return decorator


class ErrorReporter:
    """Centralized error reporting and handling."""
    
    @staticmethod
    def report_error(
        error: Exception,
        context: str = "",
        user_friendly: bool = True
    ) -> str:
        """
        Report an error with context.
        
        Args:
            error: The exception that occurred
            context: Additional context about when/where the error occurred
            user_friendly: Whether to return a user-friendly message
            
        Returns:
            Error message (user-friendly if requested)
        """
        error_details = f"{context}: {str(error)}" if context else str(error)
        
        # Log the full error
        logger.error(
            f"Error reported - {error_details}",
            exc_info=True
        )
        
        if user_friendly:
            # Return user-friendly message
            return "Sorry, something went wrong. Please try again."
        else:
            return error_details
    
    @staticmethod
    def handle_startup_error(error: Exception) -> bool:
        """
        Handle critical startup errors.
        
        Returns:
            True if the application can continue, False if it should exit
        """
        critical_errors = [
            "No module named",
            "API key",
            "Permission denied",
            "Access denied"
        ]
        
        error_str = str(error).lower()
        is_critical = any(critical in error_str for critical in critical_errors)
        
        if is_critical:
            logger.critical(f"Critical startup error: {error}")
            return False
        else:
            logger.error(f"Startup error (recoverable): {error}")
            return True


def safe_call(func: Callable, *args, **kwargs) -> tuple[bool, Any]:
    """
    Safely call a function and return success status with result.
    
    Returns:
        Tuple of (success: bool, result: Any)
    """
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        logger.error(f"Safe call failed for {func.__name__}: {e}")
        return False, None


async def safe_async_call(func: Callable, *args, **kwargs) -> tuple[bool, Any]:
    """
    Safely call an async function and return success status with result.
    
    Returns:
        Tuple of (success: bool, result: Any)
    """
    try:
        result = await func(*args, **kwargs)
        return True, result
    except Exception as e:
        logger.error(f"Safe async call failed for {func.__name__}: {e}")
        return False, None
