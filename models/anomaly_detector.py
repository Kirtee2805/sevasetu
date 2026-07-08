"""
SevaSetu — anomaly_detector.py
Team AstraSync | GEC Rajkot

WHAT THIS FILE DOES:
Detects suspicious PHC stock reports using IsolationForest.

REAL PROBLEM IT SOLVES:
PHC staff manually enter stock data.
They sometimes report wrong numbers to avoid accountability.

Example from REAL Gujarat data:
- Ahmadabad reports ZERO IFA tablets consumed
- But OPD attendance was 800+ patients
- Expected consumption = ~2400 tablets
- Ratio = 0/2400 = 0.0 (should be ~1.0)
→ SUSPICIOUS — flag this report

THIS IS YOUR #1 INNOVATION:
Every other team trusts the data. We don't.

HOW TO USE:
    from models.data_loader import load_data
    from models.feature_engineering import engineer_features
    from models.anomaly_detector import AnomalyDetector

    df = load_data()
    df = engineer_features(df)
    detector = AnomalyDetector()
    df = detector.detect(df)
"""

import pandas as pd
import numpy as np
import pickle
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class AnomalyDetector:
    """
    Detects suspicious medicine stock reports.
    Uses IsolationForest — works WITHOUT labeled data.
    Learns what NORMAL looks like, flags everything else.
    """

    # Features used for detection
    # These are the columns that best reveal suspicious patterns
    FEATURES = [
        "consumption_ratio",       # KEY: actual/expected ratio
        "log_consumption_ratio",   # log scale version
        "anomaly_signal_strength", # combined flag score
        "zero_consumption",        # zero despite patients
        "consumption_spike",       # 3x above expected
        "consumption_collapse",    # far below expected
        "stock_jump",              # stock increased without supply
        "stock_coverage_ratio",    # months of stock remaining
        "data_quality_score",      # overall data quality
        "opd_attendance",          # patient footfall
        "stockout_pressure",       # how bad is stockout
    ]

    def __init__(self, contamination: float = 0.15):
        """
        Args:
            contamination: expected % of anomalies
                0.15 = expect 15% suspicious records
                (set higher than synthetic because real data
                 has more genuine reporting issues)
        """
        self.contamination = contamination
        self.model  = IsolationForest(
            contamination = contamination,
            n_estimators  = 150,
            max_samples   = "auto",
            random_state  = 42,
            n_jobs        = -1
        )
        self.scaler    = StandardScaler()
        self.is_fitted = False

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Trains model and flags suspicious records.

        Args:
            df: dataframe from feature_engineering.py

        Returns:
            same df with new columns:
            - anomaly_detected    : 1=suspicious, 0=normal
            - anomaly_confidence  : how confident (0-1)
            - anomaly_reason      : plain English explanation
            - verification_status : label for dashboard
        """
        print("[anomaly_detector] Running anomaly detection...")

        # Only use features that exist in this dataframe
        features = [f for f in self.FEATURES if f in df.columns]
        X = df[features].fillna(0)

        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        self.is_fitted = True

        # Predict: 1=normal, -1=anomaly
        raw_pred   = self.model.fit_predict(X_scaled)
        scores     = self.model.score_samples(X_scaled)

        df = df.copy()
        df["anomaly_detected"]   = (raw_pred == -1).astype(int)
        df["anomaly_raw_score"]  = scores

        # Normalize score to 0-1 confidence
        # More negative score = more anomalous = higher confidence
        min_score = scores.min()
        max_score = scores.max()
        df["anomaly_confidence"] = (
            (scores - max_score) / (min_score - max_score + 1e-9)
        ).clip(0, 1).round(3)

        # Add reasons and labels
        df["anomaly_reason"]      = df.apply(self._explain, axis=1)
        df["verification_status"] = df["anomaly_detected"].map({
            0: "Verified",
            1: "Suspicious — Review Required"
        })

        # Print summary
        total      = len(df)
        suspicious = df["anomaly_detected"].sum()
        print(f"[anomaly_detector] Total records : {total}")
        print(f"[anomaly_detector] Suspicious    : {suspicious} ({suspicious/total*100:.1f}%)")
        print(f"[anomaly_detector] Verified      : {total - suspicious}")

        # Show top suspicious districts
        top = (
            df[df["anomaly_detected"]==1]
            .groupby("district")
            .size()
            .sort_values(ascending=False)
            .head(5)
        )
        print("\n[anomaly_detector] Most suspicious districts:")
        for dist, count in top.items():
            print(f"  {dist:<20} {count} suspicious records")

        return df

    def _explain(self, row) -> str:
        """Generate plain English reason for each anomaly."""
        if row.get("anomaly_detected", 0) == 0:
            return "Normal — data looks correct"

        ratio = row.get("consumption_ratio", 1)
        opd   = row.get("opd_attendance", 0)
        zero  = row.get("zero_consumption", 0)
        spike = row.get("consumption_spike", 0)
        jump  = row.get("stock_jump", 0)

        if zero == 1:
            return (
                f"Zero medicines dispensed despite "
                f"{int(opd):,} patient visits — "
                f"possible under-reporting"
            )
        elif spike == 1:
            return (
                f"Consumption {ratio:.1f}x above expected "
                f"for {int(opd):,} patients — "
                f"possible over-reporting or stock diversion"
            )
        elif jump == 1:
            return (
                "Stock increased without recorded supply — "
                "possible duplicate entry"
            )
        else:
            return (
                f"Statistical outlier (ratio={ratio:.2f}) — "
                "manual review recommended"
            )

    def get_suspicious(self, df: pd.DataFrame) -> pd.DataFrame:
        """Returns only suspicious records for dashboard."""
        return df[df["anomaly_detected"] == 1][[
            "district", "month", "medicine",
            "opd_attendance", "expected_consumption",
            "consumption", "consumption_ratio",
            "anomaly_confidence", "anomaly_reason",
            "verification_status"
        ]].sort_values("anomaly_confidence", ascending=False)

    def save(self, path="models/saved/anomaly_detector.pkl"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "model" : self.model,
                "scaler": self.scaler
            }, f)
        print(f"[anomaly_detector] Saved to {path}")

    def load(self, path="models/saved/anomaly_detector.pkl"):
        with open(path, "rb") as f:
            saved = pickle.load(f)
        self.model     = saved["model"]
        self.scaler    = saved["scaler"]
        self.is_fitted = True
        print(f"[anomaly_detector] Loaded from {path}")


# ─────────────────────────────────────────────────────────
# TEST — python models/anomaly_detector.py
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    from models.data_loader import load_data
    from models.feature_engineering import engineer_features

    print("=" * 55)
    print("SevaSetu — Anomaly Detector Test")
    print("=" * 55)

    # Load and engineer
    df = load_data("data/raw/B-Gujarat_May.xlsx")
    df = engineer_features(df)

    # Detect anomalies
    detector = AnomalyDetector(contamination=0.15)
    df = detector.detect(df)

    # Show suspicious records
    suspicious = detector.get_suspicious(df)
    print(f"\nTop 10 suspicious records:")
    print(suspicious[[
        "district", "medicine",
        "consumption_ratio", "anomaly_confidence", "anomaly_reason"
    ]].head(10).to_string())

    # Save
    detector.save("models/saved/anomaly_detector.pkl")
    df.to_csv("data/processed/anomaly_results.csv", index=False)
    suspicious.to_csv("data/processed/suspicious_records.csv", index=False)
    print("\nSaved: data/processed/anomaly_results.csv")
    print("Saved: data/processed/suspicious_records.csv")
    print("\nanomaly_detector.py working correctly!")