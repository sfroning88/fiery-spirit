from psycopg2 import sql
from focus_python import PROPERTY_SNAPSHOT_TABLE

QUERY = sql.SQL("""
    SELECT
        property_id::text AS property_id,
        reported_at,
        occupancy,
        total_revenues,
        repairs_maintenance,
        payroll,
        utilities,
        contract_services,
        raw_food,
        culinary_supplies,
        administrative,
        marketing_promotions,
        activities,
        other_expenses,
        controllable_expenses,
        management_fee,
        real_estate_taxes,
        insurance,
        non_controllable_expenses,
        total_expenses,
        operating_margin,
        controllable_prd,
        function
    FROM {table}
""").format(table=sql.Identifier(*PROPERTY_SNAPSHOT_TABLE))
