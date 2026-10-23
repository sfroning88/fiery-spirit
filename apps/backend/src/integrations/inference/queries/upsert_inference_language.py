from psycopg2 import sql
from fiery_python import (
    INFERENCE_LANGUAGE_TABLE,
    TRAINING_LANGUAGE_LABEL_ENUM,
    INFERENCE_ABSTAIN_REASON_ENUM,
)

QUERY = sql.SQL("""
    INSERT INTO {table}
    (
        id,
        score,
        label,
        threshold_used,
        abstention_band,
        abstained,
        abstained_reason,
        generated_text,
        latency_ms,
        inferred_at,
        artifact_id,
        volcano_id,
        created_at,
        updated_at
    )
    VALUES (
        %(id)s,
        %(score)s,
        %(label)s::{label_enum},
        %(threshold_used)s,
        %(abstention_band)s,
        %(abstained)s,
        %(abstained_reason)s::{reason_enum},
        %(generated_text)s,
        %(latency_ms)s,
        %(inferred_at)s,
        %(artifact_id)s::uuid,
        %(volcano_id)s::uuid,
        NOW(),
        NOW()
    )
    ON CONFLICT (id)
    DO UPDATE SET
        score = EXCLUDED.score,
        label = EXCLUDED.label,
        threshold_used = EXCLUDED.threshold_used,
        abstention_band = EXCLUDED.abstention_band,
        abstained = EXCLUDED.abstained,
        abstained_reason = COALESCE(EXCLUDED.abstained_reason, {table}.abstained_reason),
        generated_text = EXCLUDED.generated_text,
        latency_ms = EXCLUDED.latency_ms,
        inferred_at = COALESCE(EXCLUDED.inferred_at, {table}.inferred_at),
        updated_at = NOW()
""").format(
    table=sql.Identifier(*INFERENCE_LANGUAGE_TABLE),
    label_enum=sql.Identifier(*TRAINING_LANGUAGE_LABEL_ENUM),
    reason_enum=sql.Identifier(*INFERENCE_ABSTAIN_REASON_ENUM),
)
