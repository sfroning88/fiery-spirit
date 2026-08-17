"""
Author: Sean Froning
Created Date: 5.3.2026
Class definitions for Setting enums
"""

from enum import Enum


class DomainOption(str, Enum):
    """Worker domain enumeration"""

    API = "api"
    AI = "ai"
