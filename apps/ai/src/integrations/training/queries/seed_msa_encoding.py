from psycopg2 import sql
from focus_python import TRAINING_MSA_ENCODING_TABLE

QUERY = sql.SQL("""
    INSERT INTO {table}
        (
            batch_id, 
            msa_id, 
            mean_target, 
            sample_count, 
            updated_at
        )
    VALUES
        (%s::uuid, %s, %s, %s, NOW()) 
    ON CONFLICT (batch_id, msa_id)
    DO UPDATE SET
        mean_target = EXCLUDED.mean_target,
        sample_count = EXCLUDED.sample_count,
        updated_at = NOW()          
""").format(table=sql.Identifier(*TRAINING_MSA_ENCODING_TABLE))
