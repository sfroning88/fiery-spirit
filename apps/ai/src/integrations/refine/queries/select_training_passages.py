from psycopg2 import sql
from fiery_python import (
    TRAINING_PASSAGE_TABLE,
    TRAINING_SAMPLE_SOURCE_ENUM,
    TRAINING_SPLIT_ENUM,
    TRAINING_LANGUAGE_LABEL_ENUM,
)

QUERY = sql.SQL("""
    SELECT id::text,
        source::{source_enum},
        split::{split_enum},
        label::{label_enum},
        citation,
        published_at,
        chunk_index,
        storage_path,
        volcano_id::text
    FROM {table}
    WHERE split = %s::{split_enum}
        AND id > %s::uuid
    ORDER BY id
    LIMIT %s
""").format(
    table=sql.Identifier(*TRAINING_PASSAGE_TABLE),
    source_enum=sql.Identifier(*TRAINING_SAMPLE_SOURCE_ENUM),
    split_enum=sql.Identifier(*TRAINING_SPLIT_ENUM),
    label_enum=sql.Identifier(*TRAINING_LANGUAGE_LABEL_ENUM),
)
