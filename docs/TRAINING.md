# Training Pipeline

Last updated: **May 2026**

## Training Contract

The current training contract is:

```python
TRAINING_FUNCTION_SPLIT_VERSION = 1
```

```python
weight_splits = {
    "train": 0.70,
    "validate": 0.15,
    "test": 0.15,
}
```

```python
models = [
    "linear", # regression-based, no regularization
    "ridge", # regression-based, L2 regularization
    "lasso", # regression-based, L1 regularization
    "elasticnet", # regression-based, blended L1 + L2 regularization
    "forest", # tree-based, ...
    "gbm", # tree-based, ...
    "xgboost", # tree-based, ...
    "svr", # ..., ...
]
```

## Design Choices

### Cross Validation

The pipeline employs `GroupKFold(n_splits=5)` for cross fold validation. Each property's snapshots are kept to one side (never straddling). For each `fold(i)`, train the fold on folds `fold(1...k-1)` with sequential rotation. The fold `test_scores` are averaged into `r2_score` for the `model`.

Each `property` can have multiple `snapshots` attached, meaning rows are not independent. This renders `GroupShuffleSplit` incompatible with the pipeline. Instead, **group aware folding** keeps correlated snapshots within the same folds.

### Data Splits

To measure model capabilities accordingly, the pipeline uses **hold out** of `feature matrix X test` (categories, observations) and `target array Y test` (one dimensional prediction array) from the training data.

`msa_id_encoded` is created once globally on the full training data, and then rebuilt per fold to avoid **data leakage** (cheating on the encoded value in predictions). To indicate trustworthiness of the target mean, `count` is included.

### Pipeline Wrapping

[`Support Vector Regression`](https://en.wikipedia.org/wiki/Support_vector_machine) requires each feature to exist in relative scale to one another. The `SVR` estimator is wrapped in a `Pipeline` accordingly.

The other `training jobs` (tree and linear approaches) are **scale invariant** and fitted directly.

### Function Assignment

`TrainingGroup` is assigned at the **property level** and cascaded down to `snapshots` according to the `train`, `validate`, `test` weight splits. The split is applied once-per-shuffle, randomly, and logged in the database.

### Seed Generation

The **training seed** is constant defined via `TRAINING_SPLIT_SEED` and used for model internal randomness (XGBoost subsampling, Forest boostrapping, etc). The **shuffle seed** is either provided by the caller or defaults to the current time.

## Training Methodology

### Training Dataframe

A training dataframe is constructed upon batch creation, within the `training_job` of each `ModelType`, and within each `validate score` computation.

```python
model_count = 8 # configured training jobs
frames_created = 1 + (2 * model_count) # dataframe creations
```

The training dataframe is created by:

1. Inner merging dataframes `properties` and `snapshots`
2. Compute `msa_id_encoded` and `state_id_encoded` encodings
3. Compute each `feature column` of the current `feature contract`

### Training and Scoring

The training and scoring process for each `model`:

1. Group aware split `frame` using `GroupKFold(n_splits=5)`
2. Split `snapshots` into `X train`, `X test`, `y train`, `y test`
3. Apply `msa_id_encoded` and `state_id_encoded` with mean target
4. Fit `estimator` with the `X train`, `y train` sets
5. Calculate `test_score`, `train_score`, and `rmse` by `predict`
6. Validate `estimator` against the held out `validate` group

### Batch Operations

Each `model TrainingBatch` has its `training jobs` occur **asynchronously and concurrently** by background jobs. This is why each job builds the `frame` from scratch and why each transaction happens **atomically**.

After each `model` finishes training, selecting a winner for the batch by highest `r2_score` is attempted. If a new winner is selected, a `hot-swap` occurs to the `inference` service.

### Artifact Persistence

The trained `model` is serialized and persisted as a `.pkl` **self-consistent artifact** to `s3 models` in Supabase. The `pickle` bundle contains the fitted estimator, MSA encoding, state encoding, global mean, `feature columns`, target column, `r2_score`, `rsme`, sample count, and metadata. The `model` is logged via `model TrainingModel`.

### Missing Value Imputation

Both `training` and `inference` impute missing numeric features to `0.0` after feature engineering. This symmetric policy avoids **training-serving skew** where a model fit on `NaN`-bearing rows would receive `0.0`-imputed inputs at inference time (or vice versa). Linear models additionally cannot consume `NaN`, so unified imputation guarantees the same matrix shape across all 8 model types.

### Schema Versioning

The `training contract` is logged by database versioning:

- **`model TrainingBatch`** records each `model batch` with `feature contract`
- **`model TrainingModel`** records each individual `model` artifact metadata

This creates an **indisputable and reproducible** in-code control of how each individual `batch` was processed and groups were assigned. `TRAINING_FUNCTION_SPLIT_VERSION` lives in-code for auditability by developers and engineers.
