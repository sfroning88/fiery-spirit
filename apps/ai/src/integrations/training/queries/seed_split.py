from psycopg2 import sql
from focus_python import TRAINING_SPLIT_TABLE

QUERY = sql.SQL("""
    INSERT INTO {table}
        (
            version, 
            train_ratio, 
            validate_ratio, 
            test_ratio, 
            shuffled_at, 
            updated_at
        )
    VALUES
        (%s, %s, %s, %s, %s, NOW())
    ON CONFLICT (version) DO UPDATE
        SET train_ratio   = EXCLUDED.train_ratio,
            validate_ratio = EXCLUDED.validate_ratio,
            test_ratio    = EXCLUDED.test_ratio,
            shuffled_at   = EXCLUDED.shuffled_at,
            updated_at    = NOW()
""").format(table=sql.Identifier(*TRAINING_SPLIT_TABLE))
