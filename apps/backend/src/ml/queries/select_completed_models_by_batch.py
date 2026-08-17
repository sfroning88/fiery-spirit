from psycopg2 import sql
from focus_python import TRAINING_MODEL_TABLE, TRAINING_STATUS_ENUM

QUERY = sql.SQL("""
    SELECT type::text AS type, 
        storage_path, 
        r2_score, 
        rmse, 
        winner, 
        trained_at
    FROM {table}
    WHERE batch_id = %s::uuid 
        AND status = %s::{status_enum}
""").format(
    table=sql.Identifier(*TRAINING_MODEL_TABLE),
    status_enum=sql.Identifier(*TRAINING_STATUS_ENUM),
)
