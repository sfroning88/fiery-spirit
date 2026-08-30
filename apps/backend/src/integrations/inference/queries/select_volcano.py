from psycopg2 import sql
from fiery_python import (
    VOLCANO_TABLE,
    VOLCANO_ZONE_ENUM,
)

QUERY = sql.SQL("""
    SELECT id::text,
        name,
        country,
        zone::{zone_enum},
        latitude,
        longitude,
        elevation_m,
        volcanic_class,
        is_glaciated,
        is_instrumented,
        is_held_out
    FROM {table}
    WHERE id = %s::uuid
""").format(
    table=sql.Identifier(*VOLCANO_TABLE),
    zone_enum=sql.Identifier(*VOLCANO_ZONE_ENUM),
)
