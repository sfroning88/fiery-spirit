"""
Author: Sean Froning
Created Date: 5.3.2026
Class objects for nic schemas
"""

from typing import Optional
from ._base_focus import BaseFocus


class NICMSA(BaseFocus):
    """Normalized NIC MSA"""

    name: Optional[str] = None
    population: Optional[int] = None
