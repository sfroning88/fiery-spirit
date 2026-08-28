# Deformation Interferograms

Last updated: **August 2026**

## Deformation API

### Ingest Endpoint

`Interferograms` sources include:

- [**`Hephaestus`**](https://arxiv.org/abs/2204.09435) from the [`orion-ai-lab`](https://huggingface.co/orion-ai-lab)
- [**`Okada model`**](https://www.clawpack.org/v5.5.x/okada.html) for ground deformation

`Ingest` functions are requested via `/api/ingest`:

```python
class IngestRequest(BaseModel):
    source: TrainingSampleSource
    max_samples: int = 10

class IngestResponse(BaseModel):
    job_ids: List[str]
```

### Refine Endpoint

`Refine` functions are requested via `/api/refine`:

```python
class RefineRequest(BaseModel):
    contract_id: str

class RefineResponse(BaseModel):
    job_ids: List[str]
    version_id: str
    transform_hash: str
    cached: bool = False
```

## Feature Enforcement

The current **pixel contract** is:

```python
array_shape = (2, H, W) # phase, coherence
ops = [
    wrap_rad, # wrap phase to [-W, W]
    center_crop(patch_px), # patch_px x patch_px
    normalize, # NONE | MINMAX | ZSCORE | PERCENTILE
    coherence_min, # drop sample if below threshold
]
```

The current **packing contract** is:

```python
shard_members = [
    "{key}.phase.npy",
    "{key}.label.json",
]
```

## Design Choices

### Unrefined and Refined Samples

Unrefined interferogram `.npz` files are **content-addressed:**

```python
content_hash = hashlib.sha256(npz_bytes).hexdigest()
```

Refined shard `.tar` files are **layout-addressed:**

```python
payload = {
    "op_version", # STORAGE_OP_VERSION
    "patch_px", # crop size
    "wrap_rad", # wrap interval
    "normalize", # scale mode
    "coherence_min", # keep/drop
}
transform_hash = sha256(sorted(payload))
```

Tradeoffs of this choice:

[+] This makes reingesting samples **idempotent**
[+] This means code edits cannot reuse old `tar` files
[-] This is **disk expensive** with full-shard tree `hashes`

### Reject Invalid Samples

`TransformationRejected` errors drop the sample if:

- invalid `array_shape` against `(2, H, W)`
- invalid `array_shape` against `patch_px`
- `normalize` function fails with inputs
- `coherence` is less than threshold `coherence_min`

A low `coherence` interferogram is a bad measurement.
Attempting to apply `padding` or `normalization` would invent fringes.

## Dataset Pipeline

### Samples Flow

Deformation interferograms move through the pipeline:

1. Source from `Hephaestus` or `Okada`
2. Flush unrefined `.npz` to `r2_s3`
3. Mark `DatasetIngest`
4. Load unrefined `.npz` from `r2_s3`
5. Apply `Transformation`
6. Write `Shard`
7. Write `Manifest`
8. Flush refined `.tar` to `r2_s3`
9. Mark `DatasetVersion`

### Self Contained Artifacts

To prevent `training-serving skew` across the pipeline:

- Frozen `.tar` pixels are not `transformed` at train time
- `.npz` unrefined samples only serve as a cache
- Members use `format_version` and `op_version` (`STORAGE_OP_VERSION`)
- Dataset integrity by `content_hash` in `r2_s3`

## Samples Dataset

### Streaming Data

Using **Hugging Face** [`datasets`](https://huggingface.co/docs/datasets/en/index):

1. Read `MAX_DEFORMATION_SAMPLES` with `load_dataset`
2. Take `MAX_DEFORMATION_SAMPLES` with `dataset.take`
3. Iterate and process each `interferogram`
4. Idempotently `execute_values` by `TRAINING_DB_PAGE_SIZE`

Processing for each `interferogram`:

1. Read `insar_difference` and `insar_coherence` (clipped)
2. Assign `TrainingDeformationLabel` from `flags`
3. Yield the unrefined catalog fields

### Synthetic Fringes

To generate synthetic fringe fields:

1. Iter `index` from `MAX_DEFORMATION_SAMPLES`
2. Compute geographic numerical fields from `index`
3. Compute `channels` by [`Okada forward phase`](https://www.clawpack.org/geoclaw/Okada.htmlv)

### Refined Shards

To refine `.npz` samples to `.tar` shards:

1. Resolve `contract` to compute `transform_hash`
2. Reuse (`cache-hit`) or create (`cache-miss`) `version`
3. Stream unrefined `.npz` samples from `r2_s3`
4. Apply `Transformation` and drop if `TransformationRejected`
5. Pack `WebDataset` members; flush `.tar` shards to `r2_s3`
6. Write `manifest.json`; mark `version` done

### Data Citation

Data credits:

- **Dataset:** [huggingface.co/datasets/orion-ai-lab/Thalia](https://huggingface.co/datasets/orion-ai-lab/Thalia)
- **Codebase:** [github.com/Orion-AI-Lab/Thalia](https://github.com/Orion-AI-Lab/Thalia)

There is one required `.env` variable to stream data:

```python
HF_STREAM_TOKEN # read-only fine-grained token from Hugging Face
```
