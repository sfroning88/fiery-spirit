"""
Author: Sean Froning
Created Date: 8.17.2026
AI unit test fixtures
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("BACKEND_API_URL", "http://test-backend")
os.environ.setdefault("AUTH_TOKEN", "test-token")

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
