from psycopg2 import sql
from fiery_python import (
    TRAINING_PASSAGE_TABLE,
    TRAINING_SAMPLE_SOURCE_ENUM,
    TRAINING_SPLIT_ENUM,
    TRAINING_LANGUAGE_LABEL_ENUM,
)

QUERY = sql.SQL("""
    INSERT INTO {table}
    (
        id,
        source,
        split,
        label,
        citation,
        published_at,
        chunk_index,
        storage_path,
        volcano_id,
        created_at,
        updated_at
    )
    VALUES %s
    ON CONFLICT (id)
    DO UPDATE SET
        source = EXCLUDED.source,
        split = EXCLUDED.split,
        label = EXCLUDED.label,
        citation = EXCLUDED.citation,
        published_at = EXCLUDED.published_at,
        chunk_index = EXCLUDED.chunk_index,
        storage_path = EXCLUDED.storage_path,
        volcano_id = EXCLUDED.volcano_id,
        updated_at = NOW()
""").format(table=sql.Identifier(*TRAINING_PASSAGE_TABLE))

TEMPLATE = sql.SQL("""
    (
        %(id)s::uuid,
        %(source)s::{source_enum},
        %(split)s::{split_enum},
        %(label)s::{label_enum},
        %(citation)s,
        %(published_at)s,
        %(chunk_index)s,
        %(storage_path)s,
        %(volcano_id)s::uuid,
        NOW(),
        NOW()
    )
""").format(
    split_enum=sql.Identifier(*TRAINING_SPLIT_ENUM),
    source_enum=sql.Identifier(*TRAINING_SAMPLE_SOURCE_ENUM),
    label_enum=sql.Identifier(*TRAINING_LANGUAGE_LABEL_ENUM),
)
