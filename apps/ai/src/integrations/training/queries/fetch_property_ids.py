from psycopg2 import sql
from focus_python import PROPERTY_TABLE

QUERY = sql.SQL("""
    SELECT DISTINCT id::text AS id
    FROM {table}
""").format(table=sql.Identifier(*PROPERTY_TABLE))
