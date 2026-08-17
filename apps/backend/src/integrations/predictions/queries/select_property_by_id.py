from psycopg2 import sql
from focus_python import NIC_MSA_TABLE, PROPERTY_TABLE

QUERY = sql.SQL("""
    SELECT p.id::text AS id,
        p.name,
        p.address,
        p.city,
        p.state,
        p.zip,
        p.year_built,
        p.year_renovated,
        p.unit_size,
        p.cottage_units,
        p.independent_units,
        p.assisted_units,
        p.memory_units,
        p.total_units,
        p.total_beds,
        p.msa_id::text AS msa_id,
        m.population AS msa_population
    FROM {table} p
    LEFT JOIN {msa_table} m ON m.id = p.msa_id
    WHERE p.id = %s::uuid
    LIMIT 1
""").format(
    table=sql.Identifier(*PROPERTY_TABLE), msa_table=sql.Identifier(*NIC_MSA_TABLE)
)
