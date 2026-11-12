from psycopg2 import sql
from fiery_python import VOLCANO_TABLE

QUERY = sql.SQL("""
    SELECT id::text,
        trim(both '-' from lower(regexp_replace(
            translate(name, 'áéíóúüñÁÉÍÓÚÜÑ', 'aeiouunAEIOUUN'),
            '[^a-zA-Z0-9]+', '-', 'g'
        ))) AS name
    FROM {table}
""").format(table=sql.Identifier(*VOLCANO_TABLE))
