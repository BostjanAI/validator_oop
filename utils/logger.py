"""Logging configuration utilities.

This module provides a simple logger setup for the validation framework.
"""

from __future__ import annotations

import logging
import sys
from typing import TextIO


def setup_logger(
    name: str = "validator",
    level: int = logging.INFO,
    *,
    stream: TextIO | None = None,
    format_string: str | None = None,
    include_timestamp: bool = True,
) -> logging.Logger:
    """Configure and return a logger instance.

    Args:
        name: Logger name (default 'validator').
        level: Logging level (default INFO).
        stream: Output stream (default stdout).
        format_string: Custom format string (optional).
        include_timestamp: Include timestamp in output (default True).

    Returns:
        Configured Logger instance.

    Example:
        logger = setup_logger("my_validator", logging.DEBUG)
        logger.info("Starting validation...")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setLevel(level)

    if format_string:
        formatter = logging.Formatter(format_string)
    elif include_timestamp:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        formatter = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_logger(name: str = "validator") -> logging.Logger:
    """Get an existing logger by name.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin class that provides a logger property.

    Usage:
        class MyClass(LoggerMixin):
            def do_something(self):
                self.logger.info("Doing something...")
    """

    @property
    def logger(self) -> logging.Logger:
        """Get a logger named after this class."""
        return logging.getLogger(self.__class__.__name__)

