from psycopg2 import sql
from focus_python import PROPERTY_SNAPSHOT_TABLE, TRAINING_FUNCTION_ENUM

QUERY = sql.SQL("""
    UPDATE {table}
    SET function = data.function::{function_enum},
        updated_at = NOW()
    FROM (VALUES %s) AS data(property_id, function)
    WHERE {table}.property_id = data.property_id::uuid
""").format(
    table=sql.Identifier(*PROPERTY_SNAPSHOT_TABLE),
    function_enum=sql.Identifier(*TRAINING_FUNCTION_ENUM),
)
