from psycopg2 import sql
from focus_python import (
    PREDICTION_TYPE_ENUM,
    TRAINING_STATUS_ENUM,
    TRAINING_BATCH_TABLE,
)

QUERY = sql.SQL("""
    INSERT INTO {table}
        (
            id,
            status,
            samples,
            split_seed,
            prediction_type,
            split_version,
            updated_at
        )
    VALUES
        (%s::uuid, %s::{status_enum}, %s, %s, %s::{prediction_enum}, %s, NOW())
""").format(
    table=sql.Identifier(*TRAINING_BATCH_TABLE),
    status_enum=sql.Identifier(*TRAINING_STATUS_ENUM),
    prediction_enum=sql.Identifier(*PREDICTION_TYPE_ENUM),
)
