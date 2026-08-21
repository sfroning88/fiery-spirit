"""
Author: Sean Froning
Created Date: 8.21.2026
Main entrypoint for Fiery AI/ML API
"""

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__)))

from fiery_python import logging

# Setup structured logging
logging.setup_structured_logging()
logger = logging.get_logger(__name__)


# Training endpoint
def train_deformation(spec: Dict) -> Dict:
    return {"ok": True, "spec": spec}
