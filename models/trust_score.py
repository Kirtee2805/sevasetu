"""
SevaSetu — trust_score.py
Team AstraSync | GEC Rajkot

WHAT THIS FILE DOES:
Calculates a Trust Score for each district's PHC network.

WHAT IS TRUST SCORE?
A single number (0-100) that tells district administrators
HOW WELL each district's health system is performing
across 4 dimensions:

1. Medicine Availability  (30%) — are medicines in stock?
2. Data Reliability       (30%) — is reported data trustworthy?
3. Health System Load     (20%) — is the facility overwhelmed?
4. Service Quality        (20%) — are patients getting good care?

WHY IS THIS INNOVATIVE?
Every other team shows raw stock numbers.
We show a COMPOSITE score that tells the full story.
An MP can look at one number and immediately know
which district needs attention — without reading 50 columns.

EXAMPLE:
Rajkot    : Trust Score 72 — Grade B (Moderate)
Dang      : Trust Score 31 — Grade D (Critical Intervention Needed)
Gandhinagar: Trust Score 85 — Grade A (High Trust)

HOW TO USE:
    from models.trust_score import TrustScoreCalculator
    calc = TrustScoreCalculator()
    trust_df = calc.calculate(df)
"""

import pandas as pd
import numpy as np
import os


# Grade thresholds
GRADE_THRESHOLDS = {
    "A": 75,   # High Trust
    "B": 55,   # Moderate Trust
    "C": 35,   # Low Trust
    "D": 0,    # Critical — Intervention Needed
}

# Score weights (must sum to 100)
WEIGHTS = {
    "medicine_availability": 30,
    "data_reliability"     : 30,
    "health_system_load"   : 20,
    "service_quality"      : 20,
}


class TrustScoreCalculator:
    """
    Calculates district-level trust scores from processed HMIS data.

    Each score component is normalized to 0-100 before weighting.
    Final score = weighted sum of all components.
    """

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates trust scores for all districts.

        Args:
            df: processed dataframe with anomaly and stock features

        Returns:
            DataFrame with one row per district containing:
            - trust_score          : 0-100
            - grade                : A/B/C/D
            - grade_label          : human readable
            - component scores     : breakdown of each dimension
            - top_issue            : the biggest problem
            - recommended_action   : what to do
        """
        print("[trust_score] Calculating district trust scores...")

        records = []
        districts = df["district"].unique()

        for district in districts:
            dist_data = df[df["district"] == district]

            # ── Component 1: Medicine Availability (30%) ──────────
            # What % of medicines are NOT in critical/warning state?
            total_meds    = len(dist_data)
            critical_meds = (dist_data["alert_level"] == "CRITICAL").sum()
            warning_meds  = (dist_data["alert_level"] == "WARNING").sum()
            watch_meds    = (dist_data["alert_level"] == "WATCH").sum()

            # Weighted penalty: CRITICAL=3, WARNING=2, WATCH=1
            penalty = (critical_meds * 3 + warning_meds * 2 + watch_meds)
            max_penalty = total_meds * 3
            medicine_score = max(
                0, 100 * (1 - penalty / max(max_penalty, 1))
            )

            # ── Component 2: Data Reliability (30%) ───────────────
            # How trustworthy is the reported data?
            if "anomaly_detected" in dist_data.columns:
                anomaly_rate = dist_data["anomaly_detected"].mean()
            else:
                anomaly_rate = 0.0

            if "data_quality_score" in dist_data.columns:
                avg_data_quality = dist_data["data_quality_score"].mean()
            else:
                avg_data_quality = 0.7

            # High anomaly rate = low reliability
            data_score = (
                (1 - anomaly_rate) * 50 +
                avg_data_quality * 50
            )

            # ── Component 3: Health System Load (20%) ─────────────
            # Is the facility overwhelmed?
            avg_bed_occupancy = dist_data["bed_occupancy_rate"].mean() if "bed_occupancy_rate" in dist_data.columns else 0.5
            avg_stockout_pressure = dist_data["stockout_pressure"].mean() if "stockout_pressure" in dist_data.columns else 0.0

            # High bed occupancy is bad if also low medicine stock
            # Normalize: 0=overwhelmed, 100=well managed
            load_score = max(0, 100 * (
                (1 - avg_bed_occupancy) * 0.6 +
                (1 - min(avg_stockout_pressure / 10, 1)) * 0.4
            ))

            # ── Component 4: Service Quality (20%) ────────────────
            avg_satisfaction = dist_data["satisfaction_normalized"].mean() if "satisfaction_normalized" in dist_data.columns else 0.5
            avg_lab_coverage = min(max(dist_data["lab_coverage_rate"].mean(), 0), 1) if "lab_coverage_rate" in dist_data.columns else 0.5

            quality_score = (
                avg_satisfaction * 60 +
                avg_lab_coverage * 40
            ) * 100

            # Cap at 100
            quality_score = min(quality_score, 100)

            # ── Final Weighted Score ───────────────────────────────
            trust_score = (
                medicine_score * WEIGHTS["medicine_availability"] / 100 +
                data_score     * WEIGHTS["data_reliability"]      / 100 +
                load_score     * WEIGHTS["health_system_load"]    / 100 +
                quality_score  * WEIGHTS["service_quality"]       / 100
            )
            trust_score = round(min(max(trust_score, 0), 100), 1)

            # ── Grade ─────────────────────────────────────────────
            grade, grade_label = self._get_grade(trust_score)

            # ── Top Issue ─────────────────────────────────────────
            scores = {
                "Medicine Availability": medicine_score,
                "Data Reliability"     : data_score,
                "Health System Load"   : load_score,
                "Service Quality"      : quality_score,
            }
            top_issue = min(scores, key=scores.get)
            top_issue_score = round(scores[top_issue], 1)

            # ── Recommended Action ────────────────────────────────
            action = self._get_action(
                grade, top_issue, district,
                critical_meds, anomaly_rate
            )

            records.append({
                "district"               : district,
                "trust_score"            : trust_score,
                "grade"                  : grade,
                "grade_label"            : grade_label,
                "medicine_score"         : round(medicine_score, 1),
                "data_reliability_score" : round(data_score, 1),
                "health_load_score"      : round(load_score, 1),
                "quality_score"          : round(quality_score, 1),
                "critical_medicines"     : int(critical_meds),
                "warning_medicines"      : int(warning_meds),
                "anomaly_rate_pct"       : round(anomaly_rate * 100, 1),
                "avg_bed_occupancy_pct"  : round(avg_bed_occupancy * 100, 1),
                "top_issue"              : top_issue,
                "top_issue_score"        : top_issue_score,
                "recommended_action"     : action,
            })

        trust_df = pd.DataFrame(records).sort_values(
            "trust_score", ascending=True
        ).reset_index(drop=True)

        self._print_summary(trust_df)
        return trust_df

    def _get_grade(self, score: float) -> tuple:
        """Assign letter grade based on score."""
        if score >= GRADE_THRESHOLDS["A"]:
            return "A", "High Trust"
        elif score >= GRADE_THRESHOLDS["B"]:
            return "B", "Moderate Trust"
        elif score >= GRADE_THRESHOLDS["C"]:
            return "C", "Low Trust — Attention Needed"
        else:
            return "D", "Critical — Immediate Intervention"

    def _get_action(
        self, grade, top_issue, district,
        critical_meds, anomaly_rate
    ) -> str:
        """Generate specific recommended action."""
        if grade == "D":
            return (
                f"IMMEDIATE ACTION: {district} requires urgent district "
                f"administrator intervention. {int(critical_meds)} medicines "
                f"critically low. Worst dimension: {top_issue}."
            )
        elif grade == "C":
            if top_issue == "Data Reliability":
                return (
                    f"Conduct data audit at {district} PHCs. "
                    f"{anomaly_rate*100:.0f}% of reports flagged suspicious. "
                    f"Verify stock records manually."
                )
            elif top_issue == "Medicine Availability":
                return (
                    f"Emergency resupply needed at {district}. "
                    f"{int(critical_meds)} medicines at critical levels."
                )
            else:
                return (
                    f"Review {top_issue.lower()} at {district}. "
                    f"Schedule district health officer visit."
                )
        elif grade == "B":
            return (
                f"Monitor {district} closely. "
                f"Weakest area: {top_issue} ({self._score_label(top_issue)}). "
                f"Preventive action recommended."
            )
        else:
            return f"{district} performing well. Maintain current standards."

    def _score_label(self, issue):
        labels = {
            "Medicine Availability": "stock management",
            "Data Reliability"     : "data quality",
            "Health System Load"   : "facility capacity",
            "Service Quality"      : "patient services",
        }
        return labels.get(issue, issue.lower())

    def _print_summary(self, trust_df: pd.DataFrame):
        print(f"\n[trust_score] District Trust Score Summary:")
        print(f"  Grade A (High Trust)        : "
              f"{(trust_df['grade']=='A').sum()} districts")
        print(f"  Grade B (Moderate)          : "
              f"{(trust_df['grade']=='B').sum()} districts")
        print(f"  Grade C (Low Trust)         : "
              f"{(trust_df['grade']=='C').sum()} districts")
        print(f"  Grade D (Critical)          : "
              f"{(trust_df['grade']=='D').sum()} districts")
        print(f"\n  Average trust score: "
              f"{trust_df['trust_score'].mean():.1f}/100")

        print(f"\n  Bottom 5 districts needing attention:")
        for _, row in trust_df.head(5).iterrows():
            print(f"    {row['district']:<20} "
                  f"Score: {row['trust_score']:5.1f} | "
                  f"Grade: {row['grade']} | "
                  f"Issue: {row['top_issue']}")

        print(f"\n  Top 5 best performing districts:")
        for _, row in trust_df.tail(5).iterrows():
            print(f"    {row['district']:<20} "
                  f"Score: {row['trust_score']:5.1f} | "
                  f"Grade: {row['grade']}")


# ─────────────────────────────────────────────────────────
# TEST — python models/trust_score.py
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
    print("SevaSetu — Trust Score Calculator Test")
    print("=" * 55)

    df = load_data("data/raw/B-Gujarat_May.xlsx")
    df = engineer_features(df)
    detector = AnomalyDetector()
    df = detector.detect(df)

    calc      = TrustScoreCalculator()
    trust_df  = calc.calculate(df)

    print(f"\nFull trust score results:")
    print(trust_df[[
        "district", "trust_score", "grade",
        "medicine_score", "data_reliability_score",
        "critical_medicines", "top_issue"
    ]].to_string())

    os.makedirs("data/processed", exist_ok=True)
    trust_df.to_csv("data/processed/trust_scores.csv", index=False)
    print("\nSaved: data/processed/trust_scores.csv")
    print("\ntrust_score.py working correctly!")