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

### Schema Versioning

The `training_contract` is logged by database versioning:

- **`model TrainingContract`** records each `job_spec` to be trained with hyperparameters
- **`model TrainingSession`** records each `spawned_job` to avoid duplicate jobs
- **`model ModelArtifact`** records each individual `model` artifact metadata

This creates an **indisputable and reproducible** in-code control of each `session`.
