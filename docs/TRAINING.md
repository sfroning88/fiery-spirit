# Training Pipeline

Last updated: **August 2026**

## Design Choices

### Data Splits

It's important to accurately asses model capabilty on monitored `volcanoes`.
The pipeline tracks `is_held_out` on a per-volcano basis from the training data.

The **data leakage** concern here is training-on and cheating on the monitored volcanoes.
By keeping [**`SVZ`**](https://en.wikipedia.org/wiki/Andean_Volcanic_Belt#Southern_Volcanic_Zone) volcanoes `is_held_out=True`, accurate monitoring is possible.

### Seed Generation

The **training seed** is constant defined via `_TRAINING_SEED` per `TrainModalSpawn`.
The seed is persisted throughout the `spec` to the [`Modal workspace`](https://modal.com/docs/guide/workspaces).
The seed is used for model internal randomness (subsampling, bootstrapping, etc).

## Training Methodology

### Spawned Jobs

Each `model TrainingSession` has its `training job` occur **asynchronously** off-worker.
This is why each job builds the `spec` from scratch for a per-job `payload`.
This is also why each transaction happens **atomically** with `caching`.

### Artifact Persistence

The trained `model` (`.pkl`) is persisted as a **self-consistent artifact** to `s3`.
The `pickle` bundle contains the model itself, `job_spec`, and metadata.
The `model` is logged via `model ModelArtifact` and queried by the `model_registry`.

### Artifact Verification

First, artifacts received in `/callback/train` check for **Body MAC:**

```python
secret = ModelStorageServices._artifact_hmac_secret()
canonical = json.dumps(payload)
expected = hmac.new(
    secret, canonical.encode("utf-8"), hashlib.sha256
).hexdigest()
if not hmac.compare_digest(expected, request_hmac):
    raise error
```

Second, artifacts received in `/callback/train` check for **Object HEAD:**

```python
stored = ModelStorageServices.head_hmac(storage_path)
if not hmac.compare_digest(stored, signature):
    raise error
```

### Schema Versioning

The `training_contract` is logged by database versioning:

- **`model TrainingContract`** records each `job_spec` to be trained with hyperparameters
- **`model TrainingSession`** records each `spawned_job` to avoid duplicate jobs
- **`model ModelArtifact`** records each individual `model` artifact metadata

This creates an **indisputable and reproducible** in-code control of each `session`.

### Challenger Promotion

Via **CRON Job** any new `challengers` are evaluated for promotion over an `incumbent`.
The promotion can occur per `MODEL_REGISTRY_SLOT` from `/api/ml/promote`:

```python
MODEL_REGISTRY_SLOTS = [
    (ModelTier.CLOUD, ModelRole.SCREENER),
    (ModelTier.CLOUD, ModelRole.TEACHER),
    (ModelTier.EDGE, ModelRole.STUDENT),
]
```

First, the challenger must pass the `gate_check`:

```python
if not incumbent or challenger_metric_scores > incumbent_metric_scores:
    promote(challenger)
```

Depending on the `MODEL_REGISTRY_SLOT`, different metrics are checked:

```python
match MODEL_REGISTRY_SLOT:
    case (CLOUD, SCREENER):
        metrics = [RECALL, ABSTENTION_RATE]
    case (CLOUD, TEACHER):
        metrics = [MACRO_F1_SCORE]
    case (EDGE, STUDENT):
        metrics = [ACCURACY]
```

Second, the challenger must pass the `budget_check`:

```python
if challenger is CLOUD:
    return passed = True
if (
    flash_kb < flash_budget_kb
    and peak_ram_kb < peak_ram_budget_kb
    and macs < macs_budget
):
    return passed = True
return passed = False
```

The logged `model ModelBudget` is persisted to record each individual evaluation.
