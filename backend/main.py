"""
SevaSetu — backend/main.py
FastAPI REST API serving ML pipeline outputs for the dashboard.

All endpoints read from data/processed/ — no ML training happens here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import uvicorn

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROCESSED_DIR = ROOT / "data" / "processed"

app = FastAPI(
    title="SevaSetu API",
    description="REST API for SevaSetu Healthcare Intelligence Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Helpers ─────────────────────────────────────────────

def read_csv_safe(filename: str) -> pd.DataFrame:
    """Read a CSV from data/processed/, return empty DataFrame if missing."""
    path = PROCESSED_DIR / filename
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def read_json_safe(filename: str, default: Any = None) -> Any:
    """Read a JSON file from data/processed/."""
    path = PROCESSED_DIR / filename
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default if default is not None else {}


def df_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to list of dicts, handling NaN → None."""
    if df.empty:
        return []
    return df.fillna("").to_dict(orient="records")


# ─── Request Models ──────────────────────────────────────

class DoctorAttendanceRequest(BaseModel):
    district: str
    block: str
    phc_name: str
    doctor_present: int
    total_doctors: int


class BedStatusRequest(BaseModel):
    district: str
    block: str
    phc_name: str
    occupied_beds: int
    total_beds: int


# ═══════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.get("/")
def root():
    """Health check."""
    return {"service": "SevaSetu API", "version": "1.0.0", "status": "running"}


@app.get("/api/summary")
def get_summary():
    """Pipeline execution summary."""
    return read_json_safe("pipeline_summary.json", default={
        "status": "NO DATA",
        "records": 0,
        "districts": 0,
        "anomalies": 0,
        "critical_alerts": 0,
        "outbreaks": 0,
        "average_trust_score": 0,
    })


@app.get("/api/stockouts")
def get_stockouts(
    district: Optional[str] = Query(None),
    medicine: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
):
    """Stockout prediction results with optional filters."""
    df = read_csv_safe("stockout_results.csv")
    if df.empty:
        return {"data": [], "count": 0}

    if district:
        df = df[df["district"] == district]
    if medicine:
        df = df[df["medicine"] == medicine]
    if risk_level:
        df = df[df["risk_level"] == risk_level.upper()]

    return {"data": df_to_records(df), "count": len(df)}


@app.get("/api/alerts")
def get_alerts():
    """Critical and high-risk alerts."""
    df = read_csv_safe("critical_alerts.csv")
    return {"data": df_to_records(df), "count": len(df)}


@app.get("/api/anomalies")
def get_anomalies(district: Optional[str] = Query(None)):
    """Anomaly detection results."""
    df = read_csv_safe("anomaly_results.csv")
    if district and not df.empty:
        df = df[df["district"] == district]
    return {"data": df_to_records(df), "count": len(df)}


@app.get("/api/suspicious")
def get_suspicious():
    """Suspicious records only."""
    df = read_csv_safe("suspicious_records.csv")
    return {"data": df_to_records(df), "count": len(df)}


@app.get("/api/trust-scores")
def get_trust_scores():
    """District trust scores."""
    df = read_csv_safe("trust_scores.csv")
    return {"data": df_to_records(df), "count": len(df)}


@app.get("/api/outbreaks")
def get_outbreaks():
    """Outbreak detection results."""
    df = read_csv_safe("outbreaks.csv")
    return {"data": df_to_records(df), "count": len(df)}


@app.get("/api/recommendations")
def get_recommendations():
    """AI-generated recommendations."""
    data = read_json_safe("recommendations.json", default=[])
    if not isinstance(data, list):
        data = []
    return {"data": data, "count": len(data)}


@app.get("/api/hmis")
def get_hmis(district: Optional[str] = Query(None), medicine: Optional[str] = Query(None)):
    """Processed HMIS data."""
    df = read_csv_safe("processed_hmis.csv")
    if district and not df.empty:
        df = df[df["district"] == district]
    if medicine and not df.empty:
        df = df[df["medicine"] == medicine]
    return {"data": df_to_records(df), "count": len(df)}


@app.get("/api/phc/summary")
def get_phc_summary():
    """PHC realtime operational summary."""
    from dashboard.app import get_summary as phc_summary
    try:
        return phc_summary()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/phc/doctor-attendance")
def post_doctor_attendance(req: DoctorAttendanceRequest):
    """Update doctor attendance for a PHC."""
    from dashboard.app import update_doctor_attendance
    try:
        return update_doctor_attendance(
            req.district, req.block, req.phc_name,
            req.doctor_present, req.total_doctors,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/phc/bed-status")
def post_bed_status(req: BedStatusRequest):
    """Update bed status for a PHC."""
    from dashboard.app import update_bed_status
    try:
        return update_bed_status(
            req.district, req.block, req.phc_name,
            req.occupied_beds, req.total_beds,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/pipeline/run")
def run_pipeline():
    """Trigger a pipeline re-run (async)."""
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "models" / "run_pipeline.py")],
            capture_output=True, text=True, timeout=120,
            cwd=str(ROOT),
        )
        return {
            "status": "SUCCESS" if result.returncode == 0 else "FAILED",
            "returncode": result.returncode,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-1000:] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Pipeline timed out after 120s")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ═══════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
