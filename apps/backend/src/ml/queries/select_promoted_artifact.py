from psycopg2 import sql
from fiery_python import (
    MODEL_ARTIFACT_TABLE,
    MODEL_TIER_ENUM,
    MODEL_ROLE_ENUM,
)

QUERY = sql.SQL("""
    SELECT tier::{tier_enum},
        role::{role_enum},
        storage_path,
        promoted,
        promoted_at
    FROM {table}
    WHERE tier = %s::{tier_enum}
        AND role = %s::{role_enum}
        AND promoted = true
    ORDER BY promoted_at DESC
    LIMIT 1
""").format(
    table=sql.Identifier(*MODEL_ARTIFACT_TABLE),
    tier_enum=sql.Identifier(*MODEL_TIER_ENUM),
    role_enum=sql.Identifier(*MODEL_ROLE_ENUM),
)
