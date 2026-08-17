from psycopg2 import sql
from focus_python import (
    TRAINING_TYPE_ENUM,
    TRAINING_STATUS_ENUM,
    TRAINING_MODEL_TABLE,
)

QUERY = sql.SQL("""
    INSERT INTO {table}
        (
            type, 
            status, 
            r2_score, 
            rmse, 
            winner, 
            storage_path, 
            trained_at, 
            batch_id, 
            updated_at
                )
    VALUES
        (%s::{type_enum}, %s::{status_enum}, 0, 0, false, '', %s, %s::uuid, NOW())
""").format(
    table=sql.Identifier(*TRAINING_MODEL_TABLE),
    type_enum=sql.Identifier(*TRAINING_TYPE_ENUM),
    status_enum=sql.Identifier(*TRAINING_STATUS_ENUM),
)
