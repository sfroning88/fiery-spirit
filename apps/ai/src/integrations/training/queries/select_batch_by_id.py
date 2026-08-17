from psycopg2 import sql
from focus_python import TRAINING_MODEL_TABLE

QUERY = sql.SQL("""
            SELECT type::text AS type, 
                status::text AS status, 
                r2_score
            FROM {table}
            WHERE batch_id = %s::uuid
        """).format(table=sql.Identifier(*TRAINING_MODEL_TABLE))
