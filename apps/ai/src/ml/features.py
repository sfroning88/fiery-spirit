"""
Author: Sean Froning
Modified Date: 7.16.2026
Model training feature engineering
"""

from typing import Dict, List, Optional, Tuple
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
    PREDICTION_TARGETS,
    PredictionType,
    TrainingFunction,
    Property,
    PropertySnapshot,
    TrainingMSAEncoding,
    NICUtils,
    NumberUtils,
)
from .models import TrainingFrame


class Features:
    """Feature engineering for snapshot-level training"""

    @staticmethod
    def build_training_dataframe(
        properties: List[Property],
        snapshots: List[PropertySnapshot],
        prediction_type: PredictionType,
        function: TrainingFunction = TrainingFunction.TRAIN,
        msa_encoding: Optional[Dict[str, float]] = None,
        state_encoding: Optional[Dict[str, float]] = None,
    ) -> TrainingFrame:
        """Join each snapshot with its property features; one sample per snapshot"""
        if not properties or not snapshots:
            raise ValueError("Properties and snapshots are required for training")

        target = PREDICTION_TARGETS[prediction_type]
        filtered = [snap for snap in snapshots if snap.function == function]

        snap_df = Features._build_snapshot_df(filtered, target)
        prop_df = Features._build_property_df(properties)

        df = prop_df.merge(snap_df, on="property_id", how="inner")
        if df.empty:
            raise ValueError(
                f"No overlapping properties + snapshots after join for function={function.value}"
            )

        if msa_encoding is None:
            msa_encoding, msa_records = Features._compute_msa_encoding(df, target)
        else:
            _, msa_records = Features._compute_msa_encoding(df, target)

        if state_encoding is None:
            state_encoding = Features._compute_state_encoding(df, target)

        global_mean = float(df[target].mean())
        df[MSA_FEATURE_COLUMN] = df["msa_id"].map(msa_encoding).fillna(global_mean)
        df[STATE_FEATURE_COLUMN] = (
            df["state_id"].map(state_encoding).fillna(global_mean)
        )

        snapshot_dt = pd.to_datetime(
            df[SNAPSHOT_DATE_COLUMN].apply(lambda o: pd.Timestamp.fromordinal(int(o)))
        )
        snapshot_year = snapshot_dt.dt.year

        encoded = df[SNAPSHOT_DATE_COLUMN].map(
            lambda o: NumberUtils.encode_cyclical(int(o))
        )
        df[SNAPSHOT_MONTH_SIN_COLUMN] = encoded.map(lambda t: t[0])
        df[SNAPSHOT_MONTH_COS_COLUMN] = encoded.map(lambda t: t[1])

        df[YEARS_SINCE_RENOVATION_COLUMN] = np.where(
            df["year_renovated_ordinal"].notna(),
            snapshot_year - df["year_renovated_ordinal"],
            np.where(
                df[YEAR_BUILT_COLUMN].notna(),
                snapshot_year - df[YEAR_BUILT_COLUMN],
                0.0,
            ),
        )

        X = df[FEATURE_COLUMNS].astype(np.float64).fillna(0.0)

        return TrainingFrame(
            X=X,
            y=df[target].astype(np.float64),
            groups=df["property_id"],
            msa_id=df["msa_id"].reset_index(drop=True),
            msa_encoding=msa_encoding,
            msa_records=msa_records,
            state_id=df["state_id"].reset_index(drop=True),
            state_encoding=state_encoding,
            global_mean=global_mean,
            target=target,
        )

    @staticmethod
    def _build_snapshot_df(
        snapshots: List[PropertySnapshot], target: str
    ) -> pd.DataFrame:
        """Build and clean the snapshot-side dataframe for a given target column"""
        df = pd.DataFrame(
            [
                {
                    "property_id": snap.property_id,
                    target: NumberUtils._to_float(getattr(snap, target, None)),
                    SNAPSHOT_DATE_COLUMN: (
                        snap.reported_at.toordinal() if snap.reported_at else None
                    ),
                }
                for snap in snapshots
            ]
        )
        df = df.dropna(subset=[target, SNAPSHOT_DATE_COLUMN])
        return df[df[target] > 0]

    @staticmethod
    def _build_property_df(properties: List[Property]) -> pd.DataFrame:
        """Build the property-side dataframe with MSA, state, acuity mix, and unit columns"""
        rows = []
        for prop in properties:
            total_units = NumberUtils._to_float(prop.total_units)
            total_beds = NumberUtils._to_float(prop.total_beds)
            beds_per_unit = (
                total_beds / total_units
                if total_units and total_units > 0 and total_beds is not None
                else np.nan
            )
            rows.append(
                {
                    "property_id": prop.id,
                    "msa_id": prop.msa_id or MSA_UNKNOWN,
                    "state_id": prop.state.value if prop.state else STATE_UNKNOWN,
                    TOTAL_UNITS_COLUMN: total_units,
                    UNIT_SIZE_COLUMN: NumberUtils._to_float(prop.unit_size),
                    BEDS_PER_UNIT_COLUMN: beds_per_unit,
                    YEAR_BUILT_COLUMN: NumberUtils._to_float(prop.year_built),
                    "year_renovated_ordinal": NumberUtils._to_float(
                        prop.year_renovated
                    ),
                    MSA_POPULATION_COLUMN: NumberUtils._to_float(prop.msa_population),
                    **NICUtils._acuity_mix(prop),
                }
            )
        return pd.DataFrame(rows)

    @staticmethod
    def _compute_msa_encoding(
        df: pd.DataFrame, target: str
    ) -> Tuple[Dict[str, float], List[TrainingMSAEncoding]]:
        """Compute mean target and sample count per msa_id"""
        grouped = df.groupby("msa_id")[target].agg(["mean", "count"])
        encoding = grouped["mean"].to_dict()
        records = [
            TrainingMSAEncoding(
                msa_id=msa_id, mean_target=row["mean"], sample_count=row["count"]
            )
            for msa_id, row in grouped.iterrows()
        ]
        return encoding, records

    @staticmethod
    def _compute_state_encoding(df: pd.DataFrame, target: str) -> Dict[str, float]:
        """Compute mean target per state_id"""
        return df.groupby("state_id")[target].mean().to_dict()
