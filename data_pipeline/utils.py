# src/utils.py
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def setup_logging(verbose=False):
    """Configure the logging level and format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )


def validate_input(filepath):
    """Check whether the input path exists and is a file."""
    path = Path(filepath)

    if path.is_file():
        logger.info(f"Input file validated: {filepath}")
        return True
    else:
        logger.error(f"Input file not found: {filepath}")
        return False