import os
import logging
from pathlib import Path


ENV = os.getenv("ENV", "dev")
BASE = Path(__file__).parent


def setup_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    console.setFormatter(fmt)
    logger.addHandler(console)

    return logger
