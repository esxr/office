import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO") -> None:
    """Set up logging configuration for the Agent Office application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")

    # Configure logging
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Set debug level for third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logger = logging.getLogger("agent_office")
    logger.info(f"Logging initialized at {level} level")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: Name of the logger, will be prefixed with 'agent_office.'

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"agent_office.{name}")
    return logging.getLogger("agent_office")
