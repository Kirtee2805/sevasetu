"""
SevaSetu — feature_engineering.py
Team AstraSync | GEC Rajkot

WHAT THIS FILE DOES:
Takes the clean HMIS data from data_loader.py
and creates NEW features that help ML models predict better.

WHAT IS FEATURE ENGINEERING?
Raw data has columns like: opening_stock, consumption, closing_stock
Feature engineering creates NEW columns like:
- consumption_ratio    : actual vs expected (KEY for anomaly detection)
- stock_coverage_ratio : how many months of stock left
- consumption_spike    : flag if consumption jumped suddenly
- district_risk_score  : combined risk for each district

WHY IS THIS IMPORTANT?
ML models learn from features. Better features = better predictions.
This file is the difference between a 70% accurate model and 95% accurate.

HOW TO USE:
    from models.data_loader import load_data
    from models.feature_engineering import engineer_features
    
    df = load_data()
    df = engineer_features(df)
    df.to_csv("data/processed/processed_hmis.csv", index=False)
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import os


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main function — adds all engineered features to the dataframe.
    
    Args:
        df: clean dataframe from data_loader.py
    
    Returns:
        dataframe with new feature columns added
    """
    print("[feature_engineering] Starting feature engineering...")
    original_cols = len(df.columns)

    df = df.copy()

    # Run each feature group
    df = _stock_features(df)
    df = _consumption_features(df)
    df = _health_system_features(df)
    df = _risk_features(df)
    df = _encode_categoricals(df)

    new_cols = len(df.columns) - original_cols
    print(f"[feature_engineering] Added {new_cols} new features")
    print(f"[feature_engineering] Total columns: {len(df.columns)}")

    return df


# ─────────────────────────────────────────────────────────
# GROUP 1 — STOCK FEATURES
# ─────────────────────────────────────────────────────────
def _stock_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Features derived from stock levels.
    
    These tell the model HOW SERIOUS the stock situation is.
    """

    # Daily consumption rate
    # How many units are used per day on average?
    df["daily_consumption_rate"] = (
        df["consumption"] / 30
    ).round(2).clip(lower=0.01)

    # Stock coverage ratio
    # closing_stock / monthly_consumption
    # = how many months of stock remaining
    # 0.25 = less than 1 week remaining
    # 1.0  = exactly 1 month remaining
    # 3.0  = 3 months remaining (good buffer)
    df["stock_coverage_ratio"] = (
        df["closing_stock"] /
        df["consumption"].replace(0, 1)
    ).round(3).clip(upper=6.0)

    # Stock utilization rate
    # How much of opening stock was used?
    # Very high (>0.9) = might run out soon
    # Very low (<0.1) = possibly not dispensing medicines
    df["stock_utilization_rate"] = (
        df["consumption"] /
        df["opening_stock"].replace(0, 1)
    ).round(3).clip(upper=2.0)

    # Critical stock flag
    # Binary: 1 = will run out within 7 days
    df["is_critical_stock"] = (
        df["days_remaining"] <= 7
    ).astype(int)

    # Low stock flag
    # Binary: 1 = will run out within 14 days
    df["is_low_stock"] = (
        df["days_remaining"] <= 14
    ).astype(int)

    # Unusable stock ratio
    # High unusable = medicines expiring = waste problem
    df["unusable_ratio"] = (
        df["unusable_stock"] /
        df["opening_stock"].replace(0, 1)
    ).round(3).clip(upper=1.0)

    print("[feature_engineering] Stock features: done")
    return df


# ─────────────────────────────────────────────────────────
# GROUP 2 — CONSUMPTION FEATURES (ANOMALY DETECTION)
# ─────────────────────────────────────────────────────────
def _consumption_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Features derived from consumption patterns.
    
    THIS IS YOUR INNOVATION:
    consumption_ratio = actual / expected
    
    Normal = around 1.0
    Suspicious high = > 3.0 (consuming 3x more than expected)
    Suspicious low  = < 0.1 (barely consuming despite patients)
    """

    # consumption_ratio already exists from data_loader
    # But let's add more nuanced versions

    # Log consumption ratio
    # Log scale makes extreme values more manageable for ML
    df["log_consumption_ratio"] = np.log1p(
        df["consumption_ratio"]
    ).round(3)

    # Consumption spike flag
    # 1 = consumption is 50% above expected
    df["consumption_spike"] = (
        df["consumption_ratio"] > 1.5
    ).astype(int)

    # Consumption collapse flag
    # 1 = consumption is 50% below expected despite patients
    df["consumption_collapse"] = (
        (df["consumption_ratio"] < 0.5) &
        (df["opd_attendance"] > 100)
    ).astype(int)

    # Zero consumption flag
    # 1 = zero medicines dispensed despite patient visits
    df["zero_consumption"] = (
        (df["consumption"] == 0) &
        (df["opd_attendance"] > 50)
    ).astype(int)

    # Stock jump flag
    # 1 = closing stock much higher than opening (impossible without supply)
    df["stock_jump"] = (
        df["closing_stock"] > df["opening_stock"] * 1.5
    ).astype(int)

    # Combined anomaly signal
    # Sum of all anomaly flags — higher = more suspicious
    df["anomaly_signal_strength"] = (
        df["consumption_spike"] * 2 +    # weight 2 — most suspicious
        df["consumption_collapse"] * 2 + # weight 2 — very suspicious
        df["zero_consumption"] * 3 +     # weight 3 — most suspicious
        df["stock_jump"] * 2             # weight 2 — suspicious
    )

    print("[feature_engineering] Consumption features: done")
    return df


# ─────────────────────────────────────────────────────────
# GROUP 3 — HEALTH SYSTEM FEATURES
# ─────────────────────────────────────────────────────────
def _health_system_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Features derived from health system performance indicators.
    
    These capture HOW WELL the PHC is functioning overall,
    not just medicine stock.
    """

    # OPD load per bed
    # High value = facility is overwhelmed
    df["opd_per_bed"] = (
        df["opd_attendance"] /
        df["total_inpatients"].replace(0, 1)
    ).round(2).clip(upper=100)

    # Lab test coverage
    # lab tests / OPD = what % of patients get lab tests
    # Low value = poor diagnostic capability
    df["lab_coverage_rate"] = (
        df["lab_tests_done"] /
        df["opd_attendance"].replace(0, 1)
    ).round(3).clip(upper=2.0)

    # Patient satisfaction normalized (0 to 1)
    df["satisfaction_normalized"] = (
        df["patient_satisfaction"] / 100
    ).clip(0, 1).round(3)

    # Disease burden index
    # Combined disease cases relative to OPD
    disease_cols = [
        "childhood_diarrhoea",
        "childhood_malaria",
        "childhood_pneumonia",
        "dengue_positive"
    ]
    existing_disease = [c for c in disease_cols if c in df.columns]

    if existing_disease:
        df["disease_burden"] = df[existing_disease].sum(axis=1)
        df["disease_to_opd_ratio"] = (
            df["disease_burden"] /
            df["opd_attendance"].replace(0, 1)
        ).round(3).clip(upper=1.0)
    else:
        df["disease_burden"] = 0
        df["disease_to_opd_ratio"] = 0

    # Stockout pressure
    # stockout_rate / number of medicines = how bad is stockout problem
    df["stockout_pressure"] = df["stockout_rate"].clip(upper=10)

    print("[feature_engineering] Health system features: done")
    return df


# ─────────────────────────────────────────────────────────
# GROUP 4 — RISK FEATURES
# ─────────────────────────────────────────────────────────
def _risk_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Combined risk scores that summarize multiple signals.
    
    These are your TRUST SCORE inputs and
    OUTBREAK DETECTION inputs.
    """

    # Monsoon risk multiplier
    # Monsoon = higher disease burden = higher medicine demand
    df["monsoon_risk"] = df["is_monsoon"] * 1.3

    # Combined stock risk score (0 to 10)
    # Higher = more urgent intervention needed
    df["stock_risk_score"] = (
        (1 - df["stock_coverage_ratio"].clip(upper=1)) * 4 +  # 40% weight
        df["is_critical_stock"] * 3 +                          # 30% weight
        df["unusable_ratio"] * 2 +                             # 20% weight
        df["has_stockout"] * 1                                  # 10% weight
    ).round(2).clip(upper=10)

    # Data quality score (0 to 1)
    # 1.0 = data looks perfectly normal
    # 0.0 = data looks very suspicious
    df["data_quality_score"] = (
        1.0 -
        (df["anomaly_signal_strength"] / 9).clip(upper=1.0)
    ).round(3)

    # Overall facility risk (0 to 10)
    # Used for flagging underperforming centres
    df["facility_risk_score"] = (
        df["stock_risk_score"] * 0.4 +
        (1 - df["data_quality_score"]) * 10 * 0.3 +
        df["bed_occupancy_rate"] * 10 * 0.2 +
        df["stockout_pressure"] * 0.1
    ).round(2).clip(upper=10)

    # Outbreak risk flag
    # High ORS or paracetamol demand during monsoon = outbreak signal
    df["outbreak_risk"] = (
        (df["consumption_spike"] == 1) &
        (df["is_monsoon"] == 1) &
        (df["medicine"].isin([
            "ORS (New WHO)",
            "Paediatric Antibiotics"
        ]))
    ).astype(int)

    print("[feature_engineering] Risk features: done")
    return df


# ─────────────────────────────────────────────────────────
# GROUP 5 — ENCODE CATEGORICAL COLUMNS
# ─────────────────────────────────────────────────────────
def _encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts text columns to numbers for ML models.
    ML models need numbers, not text.
    
    LabelEncoder: Ahmadabad→0, Amreli→1, Anand→2 ...
    """
    le = LabelEncoder()

    if "medicine" in df.columns:
        df["medicine_encoded"] = le.fit_transform(df["medicine"])

    if "district" in df.columns:
        df["district_encoded"] = le.fit_transform(df["district"])

    if "alert_level" in df.columns:
        alert_map = {"NORMAL": 0, "WATCH": 1, "WARNING": 2, "CRITICAL": 3}
        df["alert_encoded"] = df["alert_level"].map(alert_map).fillna(0)

    print("[feature_engineering] Categorical encoding: done")
    return df


# ─────────────────────────────────────────────────────────
# FEATURE SUMMARY
# ─────────────────────────────────────────────────────────
def print_feature_summary(df: pd.DataFrame):
    """Prints a summary of all engineered features."""
    groups = {
        "Stock features": [
            "daily_consumption_rate", "stock_coverage_ratio",
            "stock_utilization_rate", "is_critical_stock",
            "is_low_stock", "unusable_ratio"
        ],
        "Consumption/Anomaly features": [
            "log_consumption_ratio", "consumption_spike",
            "consumption_collapse", "zero_consumption",
            "stock_jump", "anomaly_signal_strength"
        ],
        "Health system features": [
            "opd_per_bed", "lab_coverage_rate",
            "satisfaction_normalized", "disease_burden",
            "disease_to_opd_ratio", "stockout_pressure"
        ],
        "Risk features": [
            "monsoon_risk", "stock_risk_score",
            "data_quality_score", "facility_risk_score",
            "outbreak_risk"
        ],
        "Encoded features": [
            "medicine_encoded", "district_encoded", "alert_encoded"
        ],
    }

    print("\n[feature_engineering] Feature Summary:")
    for group, features in groups.items():
        existing = [f for f in features if f in df.columns]
        print(f"\n  {group} ({len(existing)}):")
        for f in existing:
            val = df[f].mean()
            print(f"    {f:<35} mean={val:.3f}")


# ─────────────────────────────────────────────────────────
# TEST — python models/feature_engineering.py
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    from models.data_loader import load_data

    print("=" * 55)
    print("SevaSetu — Feature Engineering Test")
    print("=" * 55)

    # Load real data
    df = load_data("data/raw/B-Gujarat_May.xlsx")

    if df is None:
        print("ERROR: Could not load data")
        exit(1)

    # Engineer features
    df = engineer_features(df)

    # Print summary
    print_feature_summary(df)

    # Show anomaly signals
    print(f"\nHigh anomaly signal records (signal>=3):")
    suspicious = df[df["anomaly_signal_strength"] >= 3]
    print(suspicious[[
        "district", "medicine",
        "consumption_ratio", "anomaly_signal_strength",
        "zero_consumption", "consumption_spike"
    ]].head(10))

    # Show high risk districts
    print(f"\nHigh facility risk districts (score>=7):")
    high_risk = df[df["facility_risk_score"] >= 7].groupby(
        "district"
    )["facility_risk_score"].mean().sort_values(ascending=False)
    print(high_risk.head(10))

    # Save processed file
    os.makedirs("data/processed", exist_ok=True)
    df.to_csv("data/processed/processed_hmis.csv", index=False)
    print(f"\nSaved: data/processed/processed_hmis.csv")
    print(f"Total columns: {len(df.columns)}")
    print(f"Total records: {len(df)}")
    print("\nfeature_engineering.py working correctly!")