from psycopg2 import sql
from fiery_python import (
    TRAINING_HYPERPARAMETER_LORA_LANGUAGE_TABLE,
    TRAINING_TARGET_MODULES_TABLE,
)

QUERY = sql.SQL("""
    SELECT hyperparameter_lora_language.id::text,
        hyperparameter_lora_language.rank,
        hyperparameter_lora_language.alpha,
        hyperparameter_lora_language.dropout,
        hyperparameter_lora_language.epochs,
        hyperparameter_lora_language.learning_rate,
        hyperparameter_lora_language.gradient_accumulation_steps,
        hyperparameter_lora_language.target_modules_id::text,
        target_modules.query,
        target_modules.key,
        target_modules.value,
        target_modules.output
    FROM {hyperparameter_lora_language_table} hyperparameter_lora_language
    INNER JOIN {target_modules_table} target_modules
        ON hyperparameter_lora_language.target_modules_id = target_modules.id
    WHERE hyperparameter_lora_language.id = %s::uuid
    ORDER BY hyperparameter_lora_language.created_at DESC
    LIMIT 1
""").format(
    hyperparameter_lora_language_table=sql.Identifier(
        *TRAINING_HYPERPARAMETER_LORA_LANGUAGE_TABLE
    ),
    target_modules_table=sql.Identifier(*TRAINING_TARGET_MODULES_TABLE),
)
