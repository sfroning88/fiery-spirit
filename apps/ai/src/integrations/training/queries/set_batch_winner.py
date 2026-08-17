from psycopg2 import sql
from focus_python import TRAINING_MODEL_TABLE

QUERY = sql.SQL("""
    UPDATE {table}
    SET winner = (type::text = %s), 
        updated_at = NOW()
    WHERE batch_id = %s::uuid
""").format(table=sql.Identifier(*TRAINING_MODEL_TABLE))
