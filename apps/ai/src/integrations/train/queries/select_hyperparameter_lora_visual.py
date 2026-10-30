from psycopg2 import sql
from fiery_python import (
    TRAINING_HYPERPARAMETER_LORA_VISUAL_TABLE,
    TRAINING_TARGET_MODULES_TABLE,
)

QUERY = sql.SQL("""
    SELECT hyperparameter_lora_visual.id::text,
        hyperparameter_lora_visual.rank,
        hyperparameter_lora_visual.alpha,
        hyperparameter_lora_visual.dropout,
        hyperparameter_lora_visual.epochs,
        hyperparameter_lora_visual.learning_rate,
        hyperparameter_lora_visual.target_modules_id::text,
        target_modules.query,
        target_modules.key,
        target_modules.value,
        target_modules.output
    FROM {hyperparameter_lora_visual_table} hyperparameter_lora_visual
    INNER JOIN {target_modules_table} target_modules
        ON hyperparameter_lora_visual.target_modules_id = target_modules.id
    WHERE hyperparameter_lora_visual.id = %s::uuid
    ORDER BY hyperparameter_lora_visual.created_at DESC
    LIMIT 1
""").format(
    hyperparameter_lora_visual_table=sql.Identifier(
        *TRAINING_HYPERPARAMETER_LORA_VISUAL_TABLE
    ),
    target_modules_table=sql.Identifier(*TRAINING_TARGET_MODULES_TABLE),
)
