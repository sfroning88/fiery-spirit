from psycopg2 import sql
from fiery_python import (
    TRAINING_LANGUAGE_TABLE,
    TRAINING_CONTRACT_TABLE,
    TRAINING_SIGNAL_ENUM,
)

QUERY = sql.SQL("""
    SELECT training_seismic.id::text,
        training_seismic.max_characters,
        training_seismic.class_id::text
    FROM {language_table} training_language
    INNER JOIN {contract_table} training_contract
        ON training_language.id = training_contract.language_id
    WHERE training_contract.id = %s::uuid
        AND training_contract.signal = 'language'::{signal_enum}
        AND training_contract.language_id IS NOT NULL
""").format(
    language_table=sql.Identifier(*TRAINING_LANGUAGE_TABLE),
    contract_table=sql.Identifier(*TRAINING_CONTRACT_TABLE),
    signal_enum=sql.Identifier(*TRAINING_SIGNAL_ENUM),
)
