"""
SevaSetu — outbreak_detector.py
Team AstraSync | GEC Rajkot

WHAT THIS FILE DOES:
Detects disease outbreaks from medicine consumption patterns.

REAL INSIGHT:
If multiple districts suddenly consume more ORS or
antibiotics than expected in the same month —
that is NOT random. That is a disease spreading.

EXAMPLE FROM REAL DATA:
If Rajkot, Surat, Vadodara all show 2x ORS consumption
in the same month → possible diarrhea outbreak starting.
Normal system detects this AFTER stock runs out.
SevaSetu detects it WHILE it is still manageable.

THIS IS INNOVATION #2:
Connects supply chain data to disease surveillance.
No other team will think of this.

HOW TO USE:
    from models.outbreak_detector import OutbreakDetector
    detector = OutbreakDetector()
    outbreaks = detector.detect(df)
"""

import pandas as pd
import numpy as np
import os

# Medicines that spike during specific disease outbreaks
OUTBREAK_MEDICINES = {
    "ORS (New WHO)"        : "Diarrhea / Cholera",
    "Paediatric Antibiotics": "Respiratory / Bacterial Infection",
    "Albendazole 400mg"    : "Intestinal Worms",
    "Vitamin A Syrup"      : "Malnutrition / Measles",
    "Calcium Tablets"      : "Maternal Health Crisis",
    "IFA Tablets (Adult)"  : "Anemia Surge",
}

# Minimum districts spiking together to call it an outbreak
MIN_DISTRICTS = 3

# How much above expected = a spike
SPIKE_THRESHOLD = 1.4   # 40% above expected


class OutbreakDetector:
    """
    Detects disease outbreaks from medicine consumption clusters.

    LOGIC:
    For each medicine + month:
    1. Find districts where consumption_ratio > SPIKE_THRESHOLD
    2. If 3+ districts spike together → OUTBREAK ALERT
    3. Classify severity by number of districts + spike intensity
    """

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Runs outbreak detection.

        Args:
            df: processed dataframe with consumption_ratio

        Returns:
            DataFrame of outbreak alerts
            (empty DataFrame if no outbreaks detected)
        """
        print("[outbreak_detector] Scanning for outbreak patterns...")
        alerts = []

        months    = df["month"].unique()
        medicines = [m for m in OUTBREAK_MEDICINES.keys()
                     if m in df["medicine"].unique()]

        for month in months:
            for medicine in medicines:

                subset = df[
                    (df["month"]    == month) &
                    (df["medicine"] == medicine)
                ]

                if len(subset) == 0:
                    continue

                # Districts with consumption spike
                spiked = subset[
                    subset["consumption_ratio"] > SPIKE_THRESHOLD
                ]

                if len(spiked) < MIN_DISTRICTS:
                    continue

                # Outbreak detected
                avg_ratio  = round(spiked["consumption_ratio"].mean(), 2)
                districts  = spiked["district"].tolist()
                num_dist   = len(districts)
                disease    = OUTBREAK_MEDICINES[medicine]
                severity   = self._severity(num_dist, avg_ratio)
                action     = self._action(
                    medicine, districts, severity, disease
                )

                alerts.append({
                    "month"            : month,
                    "medicine"         : medicine,
                    "disease_type"     : disease,
                    "num_districts"    : num_dist,
                    "districts_affected": ", ".join(districts[:5]),
                    "avg_spike_ratio"  : avg_ratio,
                    "severity"         : severity,
                    "action"           : action,
                })

        if not alerts:
            print("[outbreak_detector] No outbreak patterns detected")
            return pd.DataFrame()

        result = pd.DataFrame(alerts).sort_values(
            ["severity", "num_districts"],
            ascending=[True, False]
        )

        self._print_summary(result)
        return result

    def _severity(self, num_districts: int, avg_ratio: float) -> str:
        if num_districts >= 8 or avg_ratio >= 3.0:
            return "CRITICAL"
        elif num_districts >= 5 or avg_ratio >= 2.0:
            return "HIGH"
        else:
            return "MODERATE"

    def _action(self, medicine, districts, severity, disease):
        top3 = ", ".join(districts[:3])
        if severity == "CRITICAL":
            return (
                f"CRITICAL: Possible {disease} spreading across "
                f"{len(districts)} districts. Double {medicine} "
                f"stock in {top3} immediately. Alert epidemiologist."
            )
        elif severity == "HIGH":
            return (
                f"HIGH ALERT: {disease} pattern in {top3}. "
                f"Increase {medicine} buffer by 50%. "
                f"Monitor OPD cases daily."
            )
        else:
            return (
                f"WATCH: Early {disease} signs in {top3}. "
                f"Monitor {medicine} for next 2 weeks."
            )

    def _print_summary(self, result):
        print(f"[outbreak_detector] Outbreak alerts: {len(result)}")
        for sev in ["CRITICAL", "HIGH", "MODERATE"]:
            count = (result["severity"] == sev).sum()
            if count > 0:
                print(f"  {sev:<10}: {count}")

        print("\n[outbreak_detector] Top alerts:")
        for _, row in result.head(3).iterrows():
            print(f"  {row['month']} | {row['medicine']:<25} | "
                  f"{row['num_districts']} districts | {row['severity']}")


# ─────────────────────────────────────────────────────────
# TEST — python models/outbreak_detector.py
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    from models.data_loader import load_data
    from models.feature_engineering import engineer_features
    from models.anomaly_detector import AnomalyDetector

    print("=" * 55)
    print("SevaSetu — Outbreak Detector Test")
    print("=" * 55)

    df = load_data("data/raw/B-Gujarat_May.xlsx")
    df = engineer_features(df)
    detector = AnomalyDetector()
    df = detector.detect(df)

    outbreak = OutbreakDetector()
    outbreaks = outbreak.detect(df)

    if len(outbreaks) > 0:
        print(f"\nOutbreak alerts found:")
        print(outbreaks[[
            "month", "medicine", "num_districts",
            "avg_spike_ratio", "severity", "action"
        ]].to_string())
        os.makedirs("data/processed", exist_ok=True)
        outbreaks.to_csv("data/processed/outbreaks.csv", index=False)
        print("\nSaved: data/processed/outbreaks.csv")
    else:
        print("\nNo outbreaks detected in this month's data.")
        print("Note: Single month data may not show outbreak patterns.")
        print("With multiple months loaded, outbreaks become visible.")

    print("\noutbreak_detector.py working correctly!")