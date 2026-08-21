# Deformation Interferograms

Last updated: **August 2026**

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
    "patch_px", # crop size
    "wrap_rad", # wrap interval
    "normalize", # scale mode
    "coherence_min", # keep/drop
    "apply", # pipeline source
    "_split_channels", # stack layout
    "_center_crop", # crop geometry
    "_normalize", # scale function
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

1. Sourced from `Hephaestus` or `Okada`
2. Dumped unrefined `.npz` into `r2_s3`
3. Mark `DatasetIngest`
4. Load unrefined `.npz` from `r2_s3`
5. Apply `Transformation`
6. Write `Shard`
7. Write `Manifest`
8. Load refined `.tar` to `r2_s3`
9. Mark `DatasetVersion`

### Self Contained Artifacts

To prevent `training-serving skew` across the pipeline:

- Frozen `.tar` pixels are not `transformed` at train time
- `.npz` unrefined samples only serve as a cache
- Members use `format_version` instead of `transform_hash`
- Dataset integrity by `content_hash` in `r2_s3`
