from psycopg2 import sql
from focus_python import (
    TRAINING_TYPE_ENUM,
    TRAINING_STATUS_ENUM,
    TRAINING_MODEL_TABLE,
)

QUERY = sql.SQL("""
    UPDATE {table}
    SET status = %s::{status_enum},
        r2_score = %s,
        train_score = %s,
        validate_score = %s,
        rmse = %s,
        storage_path = %s,
        trained_at = %s,
        error_message = NULL,
        updated_at = NOW()
    WHERE type = %s::{type_enum}
        AND batch_id = %s::uuid
""").format(
    table=sql.Identifier(*TRAINING_MODEL_TABLE),
    status_enum=sql.Identifier(*TRAINING_STATUS_ENUM),
    type_enum=sql.Identifier(*TRAINING_TYPE_ENUM),
)
