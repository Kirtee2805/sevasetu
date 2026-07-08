"""
SevaSetu — run_pipeline.py
Master orchestration pipeline for the SevaSetu healthcare analytics platform.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.anomaly_detector import AnomalyDetector
from models.data_pipeline import DataPipeline
from models.outbreak_detector import OutbreakDetector
from models.recommender import RecommendationEngine
from models.stockout_predictor import StockoutPredictor
from models.trust_score import TrustScoreCalculator


def create_directories(base_dir: Path) -> None:
    """Create the required project directories if they do not exist."""
    for relative_path in ["data/processed", "models/saved", "logs"]:
        (base_dir / relative_path).mkdir(parents=True, exist_ok=True)


def initialize_logger(log_path: Path) -> logging.Logger:
    """Initialize the application logger for the pipeline."""
    logger = logging.getLogger("sevasetu.pipeline")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def print_banner() -> None:
    """Print the SevaSetu pipeline banner."""
    print("\n================================================")
    print("SevaSetu AI Pipeline")
    print("Google Build with AI")
    print("================================================")


def print_final_summary(summary: dict[str, Any]) -> None:
    """Print a compact pipeline summary to stdout."""
    print("\n================================================")
    print("Pipeline Completed Successfully")
    print("================================================")
    print(f"Records Processed : {summary.get('records', 0)}")
    print(f"Anomalies         : {summary.get('anomalies', 0)}")
    print(f"Critical Alerts   : {summary.get('critical_alerts', 0)}")
    print(f"Outbreaks         : {summary.get('outbreaks', 0)}")
    print(f"Execution Time    : {summary.get('execution_time_seconds', 0.0):.2f} seconds")
    print("================================================")


def save_summary(
    summary_path: Path,
    summary: dict[str, Any],
) -> None:
    """Persist the pipeline summary as JSON."""
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def ensure_empty_csv(path: Path, columns: list[str]) -> None:
    """Create an empty CSV file with the requested headers if missing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    empty_df = pd.DataFrame(columns=columns)
    empty_df.to_csv(path, index=False)


def main() -> int:
    """Execute the full SevaSetu pipeline."""
    start_time = time.perf_counter()
    base_dir = ROOT
    processed_dir = base_dir / "data" / "processed"
    saved_dir = base_dir / "models" / "saved"
    log_path = base_dir / "logs" / "pipeline.log"

    create_directories(base_dir)
    logger = initialize_logger(log_path)

    print_banner()
    logger.info("Pipeline started")

    summary: dict[str, Any] = {
        "status": "SUCCESS",
        "execution_time_seconds": 0.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "records": 0,
        "districts": 0,
        "medicines": 0,
        "anomalies": 0,
        "critical_alerts": 0,
        "outbreaks": 0,
        "average_trust_score": 0.0,
        "generated_files": [],
        "models_saved": [],
        "errors": [],
    }

    processed_df: Optional[pd.DataFrame] = None
    anomaly_df: Optional[pd.DataFrame] = None
    suspicious_df: Optional[pd.DataFrame] = None
    stockout_df: Optional[pd.DataFrame] = None
    alerts_df: Optional[pd.DataFrame] = None
    outbreaks_df: Optional[pd.DataFrame] = None
    trust_df: Optional[pd.DataFrame] = None
    recommendations: list[dict[str, Any]] = []

    try:
        logger.info("[1/6] Data Pipeline")
        print("[1/6] Data Pipeline")
        pipeline = DataPipeline(overwrite=True)
        processed_df = pipeline.run()
        processed_path = processed_dir / "processed_hmis.csv"
        summary["generated_files"].append(str(processed_path.relative_to(base_dir)))
        logger.info("Data pipeline completed")
    except Exception as exc:  # DataPipeline failure is fatal
        logger.exception("Data pipeline failed: %s", exc)
        summary["status"] = "FAILED"
        summary["errors"].append(str(exc))
        save_summary(base_dir / "data" / "processed" / "pipeline_summary.json", summary)
        print(f"Data pipeline failed: {exc}")
        return 1

    try:
        logger.info("[2/6] Anomaly Detection")
        print("[2/6] Anomaly Detection")
        detector = AnomalyDetector(contamination=0.15)
        anomaly_df = detector.detect(processed_df.copy())
        anomaly_path = processed_dir / "anomaly_results.csv"
        suspicious_path = processed_dir / "suspicious_records.csv"
        anomaly_df.to_csv(anomaly_path, index=False)
        suspicious_df = detector.get_suspicious(anomaly_df)
        suspicious_df.to_csv(suspicious_path, index=False)
        detector.save(str(saved_dir / "anomaly_detector.pkl"))
        summary["generated_files"].append(str(anomaly_path.relative_to(base_dir)))
        summary["generated_files"].append(str(suspicious_path.relative_to(base_dir)))
        summary["models_saved"].append(str((saved_dir / "anomaly_detector.pkl").relative_to(base_dir)))
        summary["anomalies"] = int(anomaly_df["anomaly_detected"].sum())
        logger.info("Anomaly detection completed")
    except Exception as exc:
        logger.exception("Anomaly detection failed: %s", exc)
        summary["errors"].append(f"anomaly_detection: {exc}")

    try:
        logger.info("[3/6] Stockout Prediction")
        print("[3/6] Stockout Prediction")
        predictor = StockoutPredictor()
        stockout_df = predictor.train_predict(anomaly_df.copy() if anomaly_df is not None else processed_df.copy())
        stockout_path = processed_dir / "stockout_results.csv"
        critical_path = processed_dir / "critical_alerts.csv"
        stockout_df.to_csv(stockout_path, index=False)
        alerts_df = predictor.get_alerts(stockout_df)
        alerts_df.to_csv(critical_path, index=False)
        predictor.save(str(saved_dir / "stockout_predictor.pkl"))
        summary["generated_files"].append(str(stockout_path.relative_to(base_dir)))
        summary["generated_files"].append(str(critical_path.relative_to(base_dir)))
        summary["models_saved"].append(str((saved_dir / "stockout_predictor.pkl").relative_to(base_dir)))
        summary["critical_alerts"] = int(alerts_df["risk_level"].eq("CRITICAL").sum())
        logger.info("Stockout prediction completed")
    except Exception as exc:
        logger.exception("Stockout prediction failed: %s", exc)
        summary["errors"].append(f"stockout_prediction: {exc}")

    try:
        logger.info("[4/6] Outbreak Detection")
        print("[4/6] Outbreak Detection")
        detector = OutbreakDetector()
        outbreaks_df = detector.detect(stockout_df.copy() if stockout_df is not None else processed_df.copy())
        outbreaks_path = processed_dir / "outbreaks.csv"
        if outbreaks_df is None or outbreaks_df.empty:
            ensure_empty_csv(
                outbreaks_path,
                ["month", "medicine", "disease_type", "num_districts", "districts_affected", "avg_spike_ratio", "severity", "action"],
            )
        else:
            outbreaks_df.to_csv(outbreaks_path, index=False)
        summary["generated_files"].append(str(outbreaks_path.relative_to(base_dir)))
        summary["outbreaks"] = int(len(outbreaks_df) if outbreaks_df is not None else 0)
        logger.info("Outbreak detection completed")
    except Exception as exc:
        logger.exception("Outbreak detection failed: %s", exc)
        summary["errors"].append(f"outbreak_detection: {exc}")

    try:
        logger.info("[5/6] Trust Score")
        print("[5/6] Trust Score")
        trust_calculator = TrustScoreCalculator()
        trust_df = trust_calculator.calculate(stockout_df.copy() if stockout_df is not None else processed_df.copy())
        trust_path = processed_dir / "trust_scores.csv"
        trust_df.to_csv(trust_path, index=False)
        summary["generated_files"].append(str(trust_path.relative_to(base_dir)))
        if trust_df is not None and not trust_df.empty:
            summary["average_trust_score"] = round(float(trust_df["trust_score"].mean()), 2)
        logger.info("Trust score completed")
    except Exception as exc:
        logger.exception("Trust score failed: %s", exc)
        summary["errors"].append(f"trust_score: {exc}")

    try:
        logger.info("[6/6] AI Recommendation")
        print("[6/6] AI Recommendation")
        recommender = RecommendationEngine(data_dir=str(processed_dir), output_path=str(processed_dir / "recommendations.json"))
        recommendations = recommender.generate_all()
        recommendations_path = processed_dir / "recommendations.json"
        summary["generated_files"].append(str(recommendations_path.relative_to(base_dir)))
        logger.info("Recommendation generation completed")
    except Exception as exc:
        logger.exception("Recommendation generation failed: %s", exc)
        summary["errors"].append(f"recommendation_generation: {exc}")

    if processed_df is not None:
        summary["records"] = int(len(processed_df))
        summary["districts"] = int(processed_df["district"].nunique()) if "district" in processed_df.columns else 0
        summary["medicines"] = int(processed_df["medicine"].nunique()) if "medicine" in processed_df.columns else 0

    summary["execution_time_seconds"] = round(time.perf_counter() - start_time, 2)
    summary_path = processed_dir / "pipeline_summary.json"
    save_summary(summary_path, summary)
    summary["generated_files"].append(str(summary_path.relative_to(base_dir)))
    save_summary(summary_path, summary)

    logger.info("Pipeline summary written to %s", summary_path)
    print_final_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
