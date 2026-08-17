"""
Author: Sean Froning
Modified Date: 7.16.2026
Unit tests for inference feature engineering
"""

from datetime import date

import pytest
from fiery_python import FEATURE_COLUMNS, NICState, NumberUtils, Property
from ml.features import Features


def test_build_predict_vector_matches_feature_columns():
    prop = Property(
        id="prop-1",
        msa_id="msa-1",
        state=NICState.CA,
        total_units=50,
        cottage_units=10,
        independent_units=10,
        assisted_units=15,
        memory_units=15,
        year_built=1995,
        year_renovated=2010,
        msa_population=500_000,
    )
    msa_encoding = {"msa-1": 12.0, "unknown": 10.0}
    state_encoding = {"CA": 11.0, "unknown": 10.0}

    frame = Features.build_predict_vector(
        prop,
        msa_encoding,
        state_encoding,
        global_mean=9.0,
        snapshot_reported_at=date(2024, 1, 15),
    )

    assert list(frame.columns) == FEATURE_COLUMNS
    assert len(frame) == 1
    assert frame["msa_id_encoded"].iloc[0] == 12.0
    assert frame["state_encoded"].iloc[0] == 11.0
    snapshot_ordinal = date(2024, 1, 15).toordinal()
    expected_sin, expected_cos = NumberUtils.encode_cyclical(snapshot_ordinal)
    assert frame["snapshot_date"].iloc[0] == snapshot_ordinal
    assert frame["snapshot_month_sin"].iloc[0] == pytest.approx(expected_sin)
    assert frame["snapshot_month_cos"].iloc[0] == pytest.approx(expected_cos)


def test_build_predict_vector_falls_back_to_global_mean_for_unknown_keys():
    prop = Property(id="prop-2", total_units=10, cottage_units=10)

    frame = Features.build_predict_vector(
        prop,
        msa_encoding={"unknown": 8.0},
        state_encoding={"unknown": 7.0},
        global_mean=5.5,
        snapshot_reported_at=date(2023, 12, 1),
    )

    assert frame["msa_id_encoded"].iloc[0] == 8.0
    assert frame["state_encoded"].iloc[0] == 7.0
