"""
SevaSetu — data_pipeline.py
Team AstraSync | GEC Rajkot

Production-ready preprocessing pipeline for HMIS healthcare data.
The pipeline loads raw Excel data, validates it, engineers features,
and exports processed datasets for downstream ML and analytics modules.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

if __package__ in {None, ""}:
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from models.data_loader import load_data
from models.feature_engineering import engineer_features


class DataPipeline:
    """End-to-end preprocessing pipeline for SevaSetu HMIS data."""

    def __init__(
        self,
        input_path: Optional[str] = None,
        output_path: Optional[str] = None,
        overwrite: bool = False,
    ) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent
        self.input_path = Path(input_path or "data/raw/B-Gujarat_May.xlsx")
        if not self.input_path.is_absolute():
            self.input_path = self.repo_root / self.input_path
        self.output_path = Path(output_path or "data/processed/processed_hmis.csv")
        if not self.output_path.is_absolute():
            self.output_path = self.repo_root / self.output_path
        self.overwrite = overwrite
        self.df: Optional[pd.DataFrame] = None
        self.summary_data: dict[str, Any] = {}

    def load(self) -> pd.DataFrame:
        """Load HMIS data from the configured Excel source."""
        print("\n====================================")
        print("SevaSetu Data Pipeline")
        print("====================================")
        print("Loading HMIS Data...")

        if not self.input_path.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_path}")

        try:
            df = load_data(str(self.input_path))
        except Exception as exc:
            raise ValueError(f"Unable to read HMIS Excel file: {exc}") from exc

        if df is None:
            raise ValueError("The HMIS loader returned an empty result")
        if df.empty:
            raise ValueError("The loaded HMIS dataframe is empty")

        self.df = df.copy()
        return self.df

    def validate(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Validate the loaded dataframe before feature engineering."""
        print("Validating Dataset...")
        frame = df if df is not None else self.df
        if frame is None:
            raise ValueError("No dataframe available for validation")
        if frame.empty:
            raise ValueError("Validation failed: dataframe is empty")

        required_columns = [
            "month",
            "district",
            "medicine",
            "opening_stock",
            "stocks_received",
            "unusable_stock",
            "consumption",
            "closing_stock",
            "expected_consumption",
            "consumption_ratio",
            "days_remaining",
            "alert_level",
            "opd_attendance",
            "patient_satisfaction",
        ]
        missing_required = [col for col in required_columns if col not in frame.columns]
        if missing_required:
            raise ValueError(
                "Validation failed: missing required columns "
                f"{missing_required}"
            )

        if frame.duplicated().any():
            duplicate_count = int(frame.duplicated().sum())
            raise ValueError(f"Validation failed: {duplicate_count} duplicate rows found")

        empty_columns = [col for col in frame.columns if frame[col].isna().all()]
        if empty_columns:
            raise ValueError(
                "Validation failed: completely empty columns found "
                f"{empty_columns}"
            )

        self._ensure_numeric_columns(frame)

        if np.isinf(frame.select_dtypes(include=[np.number]).to_numpy()).any():
            raise ValueError("Validation failed: infinite numeric values detected")

        return frame

    def preprocess(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Engineer features and apply final cleanup to the dataframe."""
        print("Engineering Features...")
        frame = df if df is not None else self.df
        if frame is None:
            raise ValueError("No dataframe available for preprocessing")

        try:
            processed = engineer_features(frame)
        except Exception as exc:
            raise ValueError(f"Feature engineering failed: {exc}") from exc

        print("Running Final Checks...")
        processed = self._finalize_dataframe(processed)
        self.df = processed
        return processed

    def _ensure_numeric_columns(self, frame: pd.DataFrame) -> None:
        """Coerce columns to numeric where appropriate and preserve categorical columns."""
        numeric_candidates = [
            col for col in frame.columns if col not in {"month", "district", "medicine", "alert_level"}
        ]
        for col in numeric_candidates:
            try:
                frame[col] = pd.to_numeric(frame[col], errors="coerce")
            except Exception:
                continue

        for col in ["month", "district", "medicine", "alert_level"]:
            if col in frame.columns:
                frame[col] = frame[col].astype("string").fillna("")

        if "month" in frame.columns:
            frame["month"] = frame["month"].astype(str).str.strip()

    def _finalize_dataframe(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Apply final sanitization and dtype corrections."""
        frame = frame.copy()
        frame = frame.replace([np.inf, -np.inf], np.nan)
        frame = frame.fillna(0)

        for col in frame.columns:
            if pd.api.types.is_numeric_dtype(frame[col]):
                frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0)

        categorical_columns = {"month", "district", "medicine", "alert_level"}
        for col in categorical_columns:
            if col in frame.columns:
                frame[col] = frame[col].astype("string").fillna("")

        for col in frame.columns:
            if col in {"month", "district", "medicine", "alert_level"}:
                continue
            if pd.api.types.is_numeric_dtype(frame[col]):
                if col.startswith("stock") or col.endswith("stock") or col in {
                    "consumption",
                    "consumption_ratio",
                    "days_remaining",
                    "opd_attendance",
                    "lab_tests_done",
                    "patient_satisfaction",
                    "bed_occupancy_rate",
                }:
                    frame[col] = frame[col].clip(lower=0)

        for col in ["opening_stock", "stocks_received", "unusable_stock", "consumption", "closing_stock"]:
            if col in frame.columns:
                frame[col] = frame[col].clip(lower=0)

        if "opd_attendance" in frame.columns:
            frame["opd_attendance"] = frame["opd_attendance"].clip(lower=0)

        if "days_remaining" in frame.columns:
            frame["days_remaining"] = frame["days_remaining"].clip(lower=0, upper=90)

        if "consumption_ratio" in frame.columns:
            frame["consumption_ratio"] = frame["consumption_ratio"].clip(lower=0, upper=10.0)

        return frame

    def save(self, path: Optional[str] = None, overwrite: Optional[bool] = None) -> Path:
        """Persist the processed dataframe to disk."""
        if self.df is None:
            raise ValueError("No processed dataframe available to save")

        target_path = Path(path or self.output_path)
        if not target_path.is_absolute():
            target_path = self.repo_root / target_path

        if target_path.exists() and not (overwrite if overwrite is not None else self.overwrite):
            raise FileExistsError(
                f"Output file already exists: {target_path}. Pass overwrite=True to replace it."
            )

        target_path.parent.mkdir(parents=True, exist_ok=True)
        self.df.to_csv(target_path, index=False)
        print("Saving Processed Dataset...")
        print(f"Saved: {target_path}")
        self.output_path = target_path
        return target_path

    def summary(self) -> dict[str, Any]:
        """Generate a quality report for the processed dataframe."""
        if self.df is None:
            raise ValueError("No processed dataframe available for reporting")

        frame = self.df
        summary = {
            "records": int(len(frame)),
            "columns": int(len(frame.columns)),
            "missing": int(frame.isna().sum().sum()),
            "duplicate_rows": int(frame.duplicated().sum()),
            "districts": int(frame["district"].nunique()) if "district" in frame.columns else 0,
            "medicines": int(frame["medicine"].nunique()) if "medicine" in frame.columns else 0,
            "date_range": {
                "start": frame["month"].min() if "month" in frame.columns else None,
                "end": frame["month"].max() if "month" in frame.columns else None,
            },
            "feature_count": int(
                len([col for col in frame.columns if col not in {"month", "district", "medicine"}])
            ),
        }
        self.summary_data = summary
        return summary

    def run(self) -> pd.DataFrame:
        """Run the complete preprocessing pipeline end-to-end."""
        start_time = time.perf_counter()
        df = self.load()
        df = self.validate(df)
        df = self.preprocess(df)
        self.save()
        summary = self.summary()
        elapsed = time.perf_counter() - start_time

        print("Pipeline Completed Successfully.")
        print(f"Records Processed: {summary['records']}")
        print(f"Features Created: {summary['feature_count']}")
        print(f"Execution Time: {elapsed:.2f}s")
        return self.df


if __name__ == "__main__":
    pipeline = DataPipeline(overwrite=True)
    processed_df = pipeline.run()
    print("\nPipeline Summary")
    print(processed_df.head(3).to_string(index=False))
