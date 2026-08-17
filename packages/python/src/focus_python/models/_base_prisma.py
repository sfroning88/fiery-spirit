"""
Author: Sean Froning
Created Date: 5.11.2026
Response models for Prisma shapes
"""

from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BasePrisma(BaseModel):
    """JSON shape aligned with @focus/db Prisma enums and models"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )
