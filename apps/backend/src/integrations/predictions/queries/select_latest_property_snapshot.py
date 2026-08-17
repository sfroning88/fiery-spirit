from psycopg2 import sql
from focus_python import PROPERTY_SNAPSHOT_TABLE

QUERY = sql.SQL("""
    SELECT reported_at::date AS reported_at
    FROM {table}
    WHERE property_id = %s::uuid
    ORDER BY reported_at DESC
    LIMIT 1
""").format(table=sql.Identifier(*PROPERTY_SNAPSHOT_TABLE))
