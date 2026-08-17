"""
Author: Sean Froning
Created Date: 5.9.2026
Database persistence for prediction inference
"""

from datetime import date, datetime
from typing import Optional
from focus_python import db_pool, logging
from focus_python.enums import PoolFetch
from focus_python import Property
from ..queries.select_property_by_id import QUERY as SELECT_PROPERTY_BY_ID
from ..queries.select_latest_property_snapshot import (
    QUERY as SELECT_LATEST_PROPERTY_SNAPSHOT,
)

logger = logging.get_logger(__name__)


class PersistServices:
    """Database persistence for inference"""

    @staticmethod
    def fetch_property(property_id: str) -> Optional[Property]:
        """Pull a single property row by id and hydrate a Property pydantic model"""
        with db_pool.get_cursor() as cursor:
            query_string = SELECT_PROPERTY_BY_ID.as_string(cursor)
        row = db_pool.run(query_string, (property_id,), fetch=PoolFetch.ONE)
        if not row:
            return None
        return Property(**row)

    @staticmethod
    def fetch_latest_snapshot_reported_at(property_id: str) -> Optional[date]:
        """Latest snapshot reported_at for the property"""
        with db_pool.get_cursor() as cursor:
            query_string = SELECT_LATEST_PROPERTY_SNAPSHOT.as_string(cursor)
        row = db_pool.run(query_string, (property_id,), fetch=PoolFetch.ONE)
        if not row:
            return None
        raw = row.get("reported_at")
        if raw is None:
            return None
        if isinstance(raw, datetime):
            return raw.date()
        return raw
