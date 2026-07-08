"""
SevaSetu — recommender.py
Team AstraSync | GEC Rajkot

This module generates actionable redistribution and operational
recommendations for PHC medicine stockout situations.

It works as the final stage of the pipeline after:
- anomaly detection
- stockout prediction
- trust scoring
- outbreak detection

The recommendation engine does not perform prediction itself.
It only translates existing risk signals into operational guidance.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

import pandas as pd

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None


class RecommendationEngine:
    """Generate operational recommendations for stockout and anomaly events."""

    def __init__(
        self,
        data_dir: str = "data/processed",
        output_path: str = "data/processed/recommendations.json",
    ) -> None:
        self.data_dir = Path(data_dir)
        self.output_path = Path(output_path)
        self.logger = self._setup_logger()
        self.client: Any = None
        self.recommendations: list[dict[str, Any]] = []
        self.stockout_df: pd.DataFrame = pd.DataFrame()
        self.anomaly_df: pd.DataFrame = pd.DataFrame()
        self.trust_df: pd.DataFrame = pd.DataFrame()
        self.outbreak_df: pd.DataFrame = pd.DataFrame()
        self._initialize_gemini()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("sevasetu.recommender")
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(levelname)s:%(name)s:%(message)s")
            )
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def _initialize_gemini(self) -> None:
        """Initialize Gemini client if API key is available."""
        if load_dotenv is not None:
            load_dotenv()

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.logger.warning("Missing GEMINI_API_KEY; using rule-based recommendations")
            return

        try:
            from google import genai

            self.client = genai.Client(api_key=api_key)
            self.logger.info("Gemini Connected")
        except Exception as exc:  # pragma: no cover - environment dependent
            self.logger.warning("Gemini initialization failed: %s", exc)
            self.client = None

    def load_data(self) -> pd.DataFrame:
        """Load and merge processed model outputs into one recommendation dataset."""
        self.logger.info("Loading recommendation data...")

        stock_path = self.data_dir / "stockout_results.csv"
        anomaly_path = self.data_dir / "anomaly_results.csv"
        trust_path = self.data_dir / "trust_scores.csv"
        outbreak_path = self.data_dir / "outbreaks.csv"

        missing_files = [
            path.name for path in [stock_path, anomaly_path, trust_path, outbreak_path]
            if not path.exists()
        ]
        if missing_files:
            self.logger.warning("Missing CSV files: %s", ", ".join(missing_files))
            return pd.DataFrame()

        self.stockout_df = pd.read_csv(stock_path)
        self.anomaly_df = pd.read_csv(anomaly_path)
        self.trust_df = pd.read_csv(trust_path)
        self.outbreak_df = pd.read_csv(outbreak_path)

        if self.stockout_df.empty:
            self.logger.warning("Stockout results are empty")
            return pd.DataFrame()

        merged = self.stockout_df.copy()

        anomaly_columns = [
            "district",
            "medicine",
            "anomaly_detected",
            "anomaly_confidence",
            "verification_status",
            "anomaly_reason",
        ]
        anomaly_subset = self._select_columns(self.anomaly_df, anomaly_columns)
        if not anomaly_subset.empty:
            merged = self._merge_frame(
                merged,
                anomaly_subset,
                left_on=["district", "medicine"],
                right_on=["district", "medicine"],
            )

        trust_columns = [
            "district",
            "trust_score",
            "grade",
            "grade_label",
        ]
        trust_subset = self._select_columns(self.trust_df, trust_columns)
        if not trust_subset.empty:
            merged = self._merge_frame(
                merged,
                trust_subset,
                left_on=["district"],
                right_on=["district"],
            )

        outbreak_columns = [
            "district",
            "medicine",
            "severity",
            "disease_type",
        ]
        outbreak_subset = self._select_columns(self.outbreak_df, outbreak_columns)
        if not outbreak_subset.empty:
            if "district" in outbreak_subset.columns:
                merged = self._merge_frame(
                    merged,
                    outbreak_subset,
                    left_on=["district", "medicine"],
                    right_on=["district", "medicine"],
                )
            elif "medicine" in outbreak_subset.columns:
                outbreak_subset = outbreak_subset.drop_duplicates(subset=["medicine"])
                merged = self._merge_frame(
                    merged,
                    outbreak_subset,
                    left_on=["medicine"],
                    right_on=["medicine"],
                )

        if "anomaly_detected" not in merged.columns:
            merged["anomaly_detected"] = 0
        if "anomaly_confidence" not in merged.columns:
            merged["anomaly_confidence"] = 0.0
        if "trust_score" not in merged.columns:
            merged["trust_score"] = 50.0
        if "grade" not in merged.columns:
            merged["grade"] = "C"
        if "grade_label" not in merged.columns:
            merged["grade_label"] = "Moderate Trust"
        if "risk_category" not in merged.columns:
            merged["risk_category"] = merged["trust_score"].apply(self._risk_category)
        if "district_rank" not in merged.columns:
            merged["district_rank"] = (
                merged["trust_score"].rank(method="min", ascending=True).astype(int)
            )

        merged["anomaly_detected"] = merged["anomaly_detected"].fillna(0).astype(int)
        merged["anomaly_confidence"] = merged["anomaly_confidence"].fillna(0.0)
        merged["trust_score"] = merged["trust_score"].fillna(50.0)
        merged["risk_level"] = merged["risk_level"].fillna("LOW")
        merged["stockout_probability"] = merged["stockout_probability"].fillna(0.0)
        merged["outbreak_present"] = (
            merged["severity"].fillna("").astype(str).ne("") if "severity" in merged.columns else False
        )
        merged["outbreak_severity"] = merged["severity"].fillna("NONE") if "severity" in merged.columns else "NONE"
        merged["anomaly_present"] = merged["anomaly_detected"].astype(int).gt(0)

        return merged

    def _select_columns(self, frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
        available = [col for col in columns if col in frame.columns]
        return frame[available].copy() if available else pd.DataFrame()

    def _merge_frame(
        self,
        left: pd.DataFrame,
        right: pd.DataFrame,
        left_on: list[str] | str,
        right_on: list[str] | str,
    ) -> pd.DataFrame:
        if right.empty:
            return left
        return left.merge(
            right,
            left_on=left_on,
            right_on=right_on,
            how="left",
            suffixes=("", "_right"),
        )

    def _risk_category(self, score: float) -> str:
        if score >= 80:
            return "Critical"
        if score >= 60:
            return "High"
        if score >= 40:
            return "Moderate"
        return "Low"

    def generate_gemini_recommendation(self, row: dict[str, Any]) -> dict[str, Any]:
        """Generate a recommendation using Gemini when available."""
        if self.client is None:
            return self.generate_fallback(row)

        context = self._build_context(row)
        prompt = (
            "You are a PHC supply operations assistant. "
            "Generate ONLY operational recommendations. No explanations. "
            "Return valid JSON with these keys: "
            "priority, recommendation, redistribution, monitoring, procurement, expected_impact.\n"
            f"District: {context['district']}\n"
            f"Medicine: {context['medicine']}\n"
            f"Stockout Probability: {context['stockout_probability']}\n"
            f"Risk Level: {context['risk_level']}\n"
            f"Trust Score: {context['trust_score']}\n"
            f"Outbreak: {context['outbreak_status']}\n"
            f"Anomaly: {context['anomaly_status']}\n"
        )

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            text = getattr(response, "text", None) or str(response)
            parsed = self._parse_gemini_response(text)
            return self._finalize_recommendation(row, parsed, generated_by="Gemini")
        except Exception as exc:  # pragma: no cover - network dependent
            self.logger.warning("Gemini request failed for %s/%s: %s", row.get("district"), row.get("medicine"), exc)
            return self.generate_fallback(row)

    def _build_context(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "district": row.get("district", "Unknown"),
            "medicine": row.get("medicine", "Unknown"),
            "stockout_probability": round(float(row.get("stockout_probability", 0.0)), 3),
            "risk_level": row.get("risk_level", "LOW"),
            "trust_score": round(float(row.get("trust_score", 50.0)), 1),
            "outbreak_status": "Yes" if bool(row.get("outbreak_present", False)) else "No",
            "anomaly_status": "Yes" if bool(row.get("anomaly_present", False)) else "No",
        }

    def _parse_gemini_response(self, text: str) -> dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

        try:
            payload = json.loads(cleaned)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            pass

        return {
            "priority": "Medium",
            "recommendation": [cleaned[:200] if cleaned else "Escalate for operational review"],
            "redistribution": "Escalate redistribution request to district operations hub",
            "monitoring": "Monitor stock status every 12 hours",
            "procurement": "Accelerate procurement review",
            "expected_impact": "Reduce stockout risk and improve service continuity",
        }

    def generate_fallback(self, row: dict[str, Any]) -> dict[str, Any]:
        """Generate a deterministic rule-based recommendation."""
        context = self._build_context(row)
        probability = float(context["stockout_probability"])
        risk_level = str(context["risk_level"]).upper()
        trust_score = float(context["trust_score"])
        outbreak = bool(row.get("outbreak_present", False))
        anomaly = bool(row.get("anomaly_present", False))

        if risk_level in {"CRITICAL", "HIGH"} or probability >= 0.75:
            priority = "Critical"
            recommendation_lines = [
                f"Initiate emergency redistribution for {context['medicine']} at {context['district']}",
                "Authorize urgent procurement escalation to district and state supply chain teams",
                "Notify the district health officer and PHC in-charge immediately",
            ]
            redistribution = "Transfer stock from the nearest high-availability district using emergency transport"
            monitoring = "Monitor inventory and consumption every 6 hours"
            procurement = "Increase procurement and open emergency supply request"
            expected_impact = "Prevent service disruption and maintain continuity of care"
        elif probability >= 0.5 or trust_score < 45:
            priority = "High"
            recommendation_lines = [
                f"Prepare a redistribution plan for {context['medicine']} at {context['district']}",
                "Increase monitoring of stock movement and patient consumption",
                "Escalate to district logistics if depletion continues",
            ]
            redistribution = "Move surplus stock from neighboring districts within 24 hours"
            monitoring = "Monitor stock status every 12 hours"
            procurement = "Review procurement buffer and replenish if needed"
            expected_impact = "Reduce the chance of a near-term stockout"
        else:
            priority = "Medium"
            recommendation_lines = [
                f"Maintain routine stock review for {context['medicine']} at {context['district']}",
                "Keep PHC inventory and OPD consumption under watch",
                "Rebalance supply if usage spikes unexpectedly",
            ]
            redistribution = "Use routine inter-district transfer only if consumption rises"
            monitoring = "Monitor stock status daily"
            procurement = "Maintain normal procurement cadence"
            expected_impact = "Keep stock stable and preserve buffer levels"

        if outbreak:
            recommendation_lines.append("Prioritize outbreak-response buffer because disease pressure is elevated")
            procurement = "Increase outbreak-specific buffer stock and procurement urgency"

        if anomaly:
            recommendation_lines.append("Validate the reported stock and consumption figures before dispatch")
            monitoring = "Cross-check inventory and consumption entries every 6 hours"

        return self._finalize_recommendation(
            row,
            {
                "priority": priority,
                "recommendation": recommendation_lines,
                "redistribution": redistribution,
                "monitoring": monitoring,
                "procurement": procurement,
                "expected_impact": expected_impact,
            },
            generated_by="Rule-Based",
        )

    def _finalize_recommendation(
        self,
        row: dict[str, Any],
        payload: dict[str, Any],
        generated_by: str,
    ) -> dict[str, Any]:
        recommendation_items = payload.get("recommendation", [])
        if isinstance(recommendation_items, str):
            recommendation_items = [recommendation_items]
        if not isinstance(recommendation_items, list):
            recommendation_items = [str(recommendation_items)]

        return {
            "district": row.get("district", "Unknown"),
            "medicine": row.get("medicine", "Unknown"),
            "priority": payload.get("priority", "Medium"),
            "recommendation": recommendation_items,
            "redistribution": payload.get("redistribution", "Monitor and reassign stock as needed"),
            "monitoring": payload.get("monitoring", "Monitor stock status every 12 hours"),
            "procurement": payload.get("procurement", "Review procurement plan"),
            "expected_impact": payload.get("expected_impact", "Reduce service disruption"),
            "generated_by": generated_by,
        }

    def generate_all(self) -> list[dict[str, Any]]:
        """Generate recommendations for every stockout-risk row."""
        self.logger.info("Generating Recommendations...")
        data = self.load_data()
        if data.empty:
            self.recommendations = []
            self.save()
            return []

        recommendations: list[dict[str, Any]] = []
        for _, row in data.iterrows():
            record = row.to_dict()
            if self.client is None:
                recommendation = self.generate_fallback(record)
            else:
                recommendation = self.generate_gemini_recommendation(record)
            recommendations.append(recommendation)

        self.recommendations = recommendations
        self.save()
        return recommendations

    def save(self, path: Optional[str] = None) -> None:
        """Persist recommendations as pretty-printed JSON."""
        target_path = Path(path or self.output_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with target_path.open("w", encoding="utf-8") as handle:
            json.dump(self.recommendations, handle, indent=2, ensure_ascii=False)
        self.logger.info("Saved recommendations.json")


if __name__ == "__main__":
    engine = RecommendationEngine()
    recommendations = engine.generate_all()

    print("\nRecommendation Summary")
    print(f"Total recommendations: {len(recommendations)}")
    if recommendations:
        for item in recommendations[:5]:
            print(
                f"- {item['district']} | {item['medicine']} | "
                f"{item['priority']} | {item['generated_by']}"
            )
