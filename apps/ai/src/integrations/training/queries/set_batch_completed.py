from psycopg2 import sql
from focus_python import TRAINING_STATUS_ENUM, TRAINING_BATCH_TABLE

QUERY = sql.SQL("""
    UPDATE {table}
    SET status = %s::{status_enum}, 
        updated_at = NOW()
    WHERE id = %s::uuid
""").format(
    table=sql.Identifier(*TRAINING_BATCH_TABLE),
    status_enum=sql.Identifier(*TRAINING_STATUS_ENUM),
)
