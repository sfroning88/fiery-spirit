"""
Author: Sean Froning
Created Date: 5.3.2026
Class objects for Focus schemas
"""

import uuid
from typing import Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel


class BaseFocus(BaseModel):
    """Base Focus Schema Model"""

    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __init__(self, **data):
        """Create initial file class object"""
        super().__init__(**data)
        self.gen_uuid_field()

    def gen_uuid_field(self) -> None:
        """Generate a 128 bit UUID"""
        if not self.id:
            self.id = str(uuid.uuid4())

    def prepare_for_storage(self, include_id: bool = True) -> tuple:
        """Convert row to batch insertion tuple"""
        raw: dict[str, object] = self.model_dump(mode="python")

        def storage_value(value: object) -> object:
            if isinstance(value, Enum):
                return value.value
            return value

        skip = {"id"} if not include_id else set()
        return tuple(
            storage_value(raw[name])
            for name in type(self).model_fields
            if name not in skip
        )
