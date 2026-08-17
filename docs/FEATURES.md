# Feature Engineering

Last updated: **May 2026**

## Feature Contract

The current feature contract is:

```python
TRAINING_FEATURE_SCHEMA_VERSION = 7
```

```python
features = [
    pct_cottage, # derived: % of total_units that are nic_acuity == cottage
    pct_il, # derived: % of total_units that are nic_acuityy == il
    pct_al, # derived: % of total_units that are nic_acuity == al
    pct_mc, # derived: % of total_units that are nic_acuity == mc
    beds_per_unit, # derived: total_beds / total_units
    msa_id_encoded, # mean-target encoded with match presence
    msa_population, # msa information
    state_id_encoded, # mean-target encoded with match presence
    snapshot_date, # temporal field with ordinal casting (days since origin)
    snapshot_month_sin, # temporal field with cyclical encoding
    snapshot_month_cos, # temporal field with cyclical encoding
    total_units, # property information
    unit_size, # property information
    year_built, # property information
    years_since_renovation, # derived: snapshot_year - year_renovated OR year_built
]
```

All features are **`float64`** and **`order-enforced`** for consistent expectations and usage.

## Design Choices

### Temporal Engineering

The `years_since_renovation` field is calcualated as years since last snapshot, not years since current year. This makes the feature **time stable** regardless of when training runs.

The `snapshot_reported_at` field defaults to today if no date is recorded, which allows **day-over-day drift** if no snapshot is available for a property.

The `snapshot_date` field is stored as a `integer` **[`proleptic Gregorian ordinal`](https://en.wikipedia.org/wiki/Proleptic_Gregorian_calendar)**, meaning "days since years 1".

Tradeoffs of this choice:

[+] This preserves **ordering and distance** of relative `snapshot_dates`
[+] This allows trees to split on `snapshot_date` like any other numeric
[+] This avoids **cyclical encoding** using `sin` or `cos` per month
[-] This fails to capture **seasonality** and **cyclical trends**

### Mean Encoding

Also considered `target encoding`. Rather than cast `nic_msa` and `state` to a **label encoding**, the fields are applied a **mean encoding** of the `target_variable(s)`. The encoding is rebuilt **once-per-fold** during cross validation based on each fold's training portion only.

By employing **mean encoding**, models capture the relationship between categories and the target variable(s). Additionally, leaking information to the encoded entity reduces overfitting. To reduce sensitivity to outliers, `count` of samples per `nic_msa` is recorded.

If a property is missing an associated `nic_msa`, then encoding is assigned using a `global_mean` to avoid **training-serving skew**. Skew means that the `feature pipeline` at training time and at inference time produce different outputs (as a result of methodology and process).

The `global_mean` is computed at training time as the mean of the target variable across all training rows. It is **persisted in the model artifact** alongside the `msa_encoding` and `state_encoding` dictionaries so inference can apply the **same fallback** when an unseen `msa_id_encoded` or `state` is encountered at prediction time.

Alternative encoding strategies include:

- **One-Hot Encoding** using `0` or `1` to merely indicate the presence of each unique category
- **Frequencey Encoding** to capture the relative frequency (`mode`) of a category within the dataset
- **Leave-One-Out Encoding** to capture mean target but leaving out the target value being encoded

### Cyclical Encoding

Two additionally derived fields, `snapshot_month_sin` and `snapshot_month_cos`, capture seasonal trends based on the `month` of the original `snapshot_dt`. By employing **cyclical encoding**, models capture seasonal trends (summer `occupancy` spikes) and wrap-around context (`Dec` being adjacent to `Jan`).

### Ratio Heavy

The `feature contract` relies heavily on **derived ratios** (ie `pct_cottage`, `beds_per_unit`, etc). This naturally decouples building size from building mix, capturing the **scale invariant** intent. This is supplemented by an `orthogonal feature contract` that includes `total_units`.

### Interaction Terms

There are no `interaction features` in the current `feature contract`. By nature of simultaneously training and evaluating 8+ models that blend **tree** and **regression** approaches, we avoid skewing model results with custom interactions. **Tree** approaches (`Forest`, `GBM`, `XGBoost`) learn interactions automatically through exploration whereas **linear** approaches forfeit capturing interactions.

## Feature Pipeline

### Schema Versioning

The `feature contract` is logged by database versioning:

- **`model TrainingMSAEncoding`** records `msa_id_encoded` used per `feature_contract`
- **`model TrainingFeature`** records the `feature_contract` used per batch

This creates an **indisputable and reproducible** in-code control of how each individual `estimator` was trained and fitted. `TRAINING_FEATURE_SCHEMA_VERSION` lives in-code for auditability by developers and engineers.

### Self Contained Artifacts

Each persisted `.pkl` model carries everything needed to reproduce its feature transformation within the artifact at inference time. This includes the fitted estimator, the `msa_encoding` dict, the `global_mean` fallback, and the `feature contract`. This eliminates pipeline-drift issues and allows old models to remain servable without external coordination.

### Future Considerations

Intending to implement the following alterations:

- **missing indicator** columns that survive imputation
- **region relative** features for `properties` relative to market
- **interaction terms** for **linear** models performance boosts
