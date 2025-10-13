import os
import logging
from pathlib import Path


ENV = os.getenv("ENV", "dev")
BASE = Path(__file__).parent

# Configure logging before any other imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)