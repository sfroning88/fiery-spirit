"""
Author: Sean Froning
Modified Date: 7.16.2026
Unit tests for training feature engineering
"""

from datetime import date
from decimal import Decimal

import pytest
from focus_python import (
    FEATURE_COLUMNS,
    NICState,
    NumberUtils,
    PredictionType,
    Property,
    PropertySnapshot,
    TrainingFunction,
)
from ml.features import Features


def _property(**overrides):
    base = dict(
        id="prop-1",
        msa_id="msa-1",
        state=NICState.TX,
        total_units=100,
        cottage_units=10,
        independent_units=20,
        assisted_units=30,
        memory_units=40,
        year_built=2000,
    )
    base.update(overrides)
    return Property(**base)


def _snapshot(**overrides):
    base = dict(
        property_id="prop-1",
        reported_at=date(2024, 6, 1),
        controllable_prd=Decimal("12.5"),
        function=TrainingFunction.TRAIN,
    )
    base.update(overrides)
    return PropertySnapshot(**base)


def test_build_training_dataframe_joins_property_and_snapshot():
    frame = Features.build_training_dataframe(
        [_property()],
        [_snapshot()],
        PredictionType.CONTROLLABLE_PRD,
    )
    assert len(frame.X) == 1
    assert list(frame.X.columns) == FEATURE_COLUMNS
    assert frame.target == "controllable_prd"
    assert float(frame.y.iloc[0]) == pytest.approx(12.5)
    expected_sin, expected_cos = NumberUtils.encode_cyclical(
        date(2024, 6, 1).toordinal()
    )
    assert frame.X["snapshot_month_sin"].iloc[0] == pytest.approx(expected_sin)
    assert frame.X["snapshot_month_cos"].iloc[0] == pytest.approx(expected_cos)


def test_build_training_dataframe_requires_non_empty_inputs():
    with pytest.raises(ValueError, match="required"):
        Features.build_training_dataframe([], [], PredictionType.CONTROLLABLE_PRD)


def test_build_training_dataframe_respects_function_filter():
    train_snap = _snapshot(
        function=TrainingFunction.TRAIN, controllable_prd=Decimal("10.0")
    )
    test_snap = _snapshot(
        function=TrainingFunction.TEST, controllable_prd=Decimal("99.0")
    )
    frame = Features.build_training_dataframe(
        [_property()],
        [train_snap, test_snap],
        PredictionType.CONTROLLABLE_PRD,
        function=TrainingFunction.TRAIN,
    )
    assert len(frame.X) == 1
    assert float(frame.y.iloc[0]) == pytest.approx(10.0)


def test_build_snapshot_df_drops_non_positive_targets():
    df = Features._build_snapshot_df(
        [_snapshot(controllable_prd=Decimal("0"))],
        "controllable_prd",
    )
    assert df.empty
