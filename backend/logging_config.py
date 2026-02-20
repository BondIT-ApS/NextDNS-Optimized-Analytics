# file: backend/logging_config.py
import logging
import os
import sys


def setup_logging():
    """
    Set up centralized logging configuration based on LOG_LEVEL environment variable.

    LOG_LEVEL options:
    - DEBUG: Detailed information for debugging
    - INFO: General information about program execution (default)
    - WARNING: Warning messages for unexpected situations
    - ERROR: Error messages for serious problems
    - CRITICAL: Critical errors that may cause the program to abort
    """
    # Get log level from environment variable, default to INFO
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()

    # Map string to logging level
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    log_level = log_levels.get(log_level_str, logging.INFO)

    # Create formatter for log messages
    if log_level == logging.DEBUG:
        # More detailed format for debugging
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        # Cleaner format for production
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Create console handler with custom formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Get root logger and clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.setLevel(log_level)

    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info(f"📋 Logging configured with level: {log_level_str}")

    # Suppress noisy third-party loggers in production
    if log_level > logging.DEBUG:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("apscheduler").setLevel(logging.WARNING)
        logging.getLogger("werkzeug").setLevel(logging.WARNING)

    # Align uvicorn loggers so HTTP access logs respect our level setting
    for uvicorn_logger in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(uvicorn_logger).setLevel(log_level)

    return logger


def apply_log_level(level: str) -> None:
    """Change the root logger level at runtime without full reconfiguration.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level = log_levels.get(level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    for handler in root_logger.handlers:
        handler.setLevel(log_level)

    # Re-apply third-party suppression when not in DEBUG
    if log_level > logging.DEBUG:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("apscheduler").setLevel(logging.WARNING)
        logging.getLogger("werkzeug").setLevel(logging.WARNING)

    # Align uvicorn loggers so HTTP access logs respect our level setting
    for uvicorn_logger in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(uvicorn_logger).setLevel(log_level)


def get_logger(name):
    """
    Get a logger instance with the specified name.

    Args:
        name (str): Logger name (usually __name__)

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)
