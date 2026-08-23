"""
Author: Sean Froning
Created Date: 8.22.2026
Request models for Refine
"""

from pydantic import BaseModel


class RefineRequest(BaseModel):
    """Request model for running refine job"""

    contract_id: str
