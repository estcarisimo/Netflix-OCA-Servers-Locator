"""
Logging configuration and utilities.

This module provides centralized logging configuration using loguru.
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from ..config.settings import Settings


def setup_logging(
    settings: Settings,
    log_file: Path | None = None,
    verbose: bool = False,
) -> None:
    """
    Configure application-wide logging.

    Parameters
    ----------
    settings : Settings
        Application settings.
    log_file : Optional[Path]
        Log file path. If None, uses settings default.
    verbose : bool
        Enable verbose (DEBUG) logging.
    """
    # Remove default logger
    logger.remove()

    # Determine log level
    level = "DEBUG" if verbose else settings.log_level

    # Console logging format
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # Simplified format for INFO and above
    simple_format = (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<level>{message}</level>"
    )

    # Add console handler
    logger.add(
        sys.stderr,
        format=console_format if verbose else simple_format,
        level=level,
        colorize=True,
        backtrace=verbose,
        diagnose=verbose,
    )

    # Add file handler if specified
    if log_file or settings.log_file:
        file_path = log_file or Path(settings.log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            file_path,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",  # Always log everything to file
            rotation="10 MB",
            retention="1 week",
            compression="zip",
            backtrace=True,
            diagnose=True,
        )

        logger.info(f"Logging to file: {file_path}")


def log_application_start(settings: Settings) -> None:
    """
    Log application startup information.

    Parameters
    ----------
    settings : Settings
        Application settings.
    """
    logger.info(f"Starting {settings.app_name} v{settings.version}")
    logger.debug(f"Debug mode: {settings.debug}")
    logger.debug(f"Log level: {settings.log_level}")
    logger.debug(f"Request timeout: {settings.request_timeout}s")
    logger.debug(f"Max retries: {settings.max_retries}")


class InterceptHandler:
    """
    Handler to intercept standard logging and redirect to loguru.

    This allows libraries using standard logging to work with loguru.
    """

    @staticmethod
    def emit(record) -> None:
        """Emit a log record."""
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == __file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )
