# Runtime Inference

Last updated: **May 2026**

## Serving Service

### Model Serialization

Each `model` is retrieved from its `s3 location` as a **self-consistent artifact** `.pkl` file. The registry saves the model to disk in the local in-memory process. The artifact bundle allows the estimator to be fully loaded without `training-serving skew`.

Rigorous **model lineage** allows for tracking batch parameters, `feature contracts`, encodings, and `hyperparameters` to track performance changes and identify model drift.

### Model Warmup

Upon service start, **hot loading** prevents `cold start latency` with a `lifespan` event. This allows for immediate inference from `apps/dashboard` upon startup completion for the most recent batch winner.

### Model Registry

The `load` method can be called with `multi_enabled = [True|False]` to load either winner-only or all models from the most recent batch. By default, only the winner is loaded. A force reload can be triggered via `force = True`.

The registry relies on **hot swapping** to use the best available model, triggerable one of two ways:

1. Automatic webhook trigger from `apps/ai` upon batch completion with **winner promotion**
2. `jobs/dispatch_models_reload` as a **fail-safe** to asynchronously check for new winners

### Prediction Requests

To make `predictions`, the given `property_id` fetches and casts `X predict` and loads encodings. With the models **warm loaded** the estimator(s) are called with `predict` to return prediction response(s).
