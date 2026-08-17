"""
Author: Sean Froning
Modified Date: 7.16.2026
Model inference feature engineering
"""

from datetime import date, datetime, timezone
from math import isnan
from typing import Dict, Optional
import numpy as np
import pandas as pd
from focus_python import (
    BEDS_PER_UNIT_COLUMN,
    FEATURE_COLUMNS,
    MSA_FEATURE_COLUMN,
    MSA_POPULATION_COLUMN,
    MSA_UNKNOWN,
    SNAPSHOT_DATE_COLUMN,
    SNAPSHOT_MONTH_SIN_COLUMN,
    SNAPSHOT_MONTH_COS_COLUMN,
    STATE_FEATURE_COLUMN,
    STATE_UNKNOWN,
    TOTAL_UNITS_COLUMN,
    UNIT_SIZE_COLUMN,
    YEAR_BUILT_COLUMN,
    YEARS_SINCE_RENOVATION_COLUMN,
    NICUtils,
    NumberUtils,
    Property,
)


class Features:
    """Feature engineering for property-level inference"""

    @staticmethod
    def build_predict_vector(
        prop: Property,
        msa_encoding: Dict[str, float],
        state_encoding: Dict[str, float],
        global_mean: float,
        snapshot_reported_at: Optional[date] = None,
    ) -> pd.DataFrame:
        """Build a single-row inference DataFrame matching FEATURE_COLUMNS"""
        ref_date = snapshot_reported_at or datetime.now(timezone.utc).date()
        ref_ordinal = ref_date.toordinal()

        msa_value = str(prop.msa_id or MSA_UNKNOWN)
        msa_encoded = msa_encoding.get(
            msa_value, msa_encoding.get(MSA_UNKNOWN, global_mean)
        )

        state_value = prop.state.value if prop.state else STATE_UNKNOWN
        state_encoded = state_encoding.get(
            state_value, state_encoding.get(STATE_UNKNOWN, global_mean)
        )

        total_units_raw = NumberUtils._to_float(prop.total_units)
        total_units = 0.0 if isnan(total_units_raw) else total_units_raw
        total_beds = NumberUtils._to_float(prop.total_beds)
        beds_per_unit = (
            total_beds / total_units
            if total_units > 0 and not isnan(total_beds)
            else 0.0
        )

        year_built = NumberUtils._to_float(prop.year_built)
        year_renovated = NumberUtils._to_float(prop.year_renovated)
        snapshot_year = float(ref_date.year)
        snapshot_month_sin, snapshot_month_cos = NumberUtils.encode_cyclical(
            ref_ordinal
        )
        years_since_renovation = (
            snapshot_year - year_renovated
            if not isnan(year_renovated)
            else snapshot_year - year_built if not isnan(year_built) else 0.0
        )

        msa_population_raw = NumberUtils._to_float(prop.msa_population)
        unit_size_raw = NumberUtils._to_float(prop.unit_size)

        row = {
            **NICUtils._acuity_mix(prop),
            BEDS_PER_UNIT_COLUMN: beds_per_unit,
            MSA_FEATURE_COLUMN: msa_encoded,
            MSA_POPULATION_COLUMN: (
                0.0 if isnan(msa_population_raw) else msa_population_raw
            ),
            SNAPSHOT_DATE_COLUMN: ref_ordinal,
            SNAPSHOT_MONTH_SIN_COLUMN: snapshot_month_sin,
            SNAPSHOT_MONTH_COS_COLUMN: snapshot_month_cos,
            STATE_FEATURE_COLUMN: state_encoded,
            TOTAL_UNITS_COLUMN: total_units,
            UNIT_SIZE_COLUMN: 0.0 if isnan(unit_size_raw) else unit_size_raw,
            YEAR_BUILT_COLUMN: 0.0 if isnan(year_built) else year_built,
            YEARS_SINCE_RENOVATION_COLUMN: years_since_renovation,
        }
        return pd.DataFrame([row], columns=FEATURE_COLUMNS).astype(np.float64)
