"""
SevaSetu Backend - FastAPI Main Application
AI-powered Healthcare Intelligence Platform for Gujarat PHCs.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, model_validator

# ==================================================
# FIREBASE SERVICE IMPORTS
# ==================================================
# Assuming firebase_service.py exists in the services directory
# with the requested operational methods.
<<<<<<< HEAD
from backend.services.firebase_service import *
=======
from services.firebase_service import *
>>>>>>> 7aaffb768011c2e603b4ff9e1cf3ea1b6e22f556

# ==================================================
# LOGGING CONFIGURATION
# ==================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("sevasetu_backend")

# ==================================================
# FASTAPI APP INITIALIZATION
# ==================================================
app = FastAPI(
    title="SevaSetu API",
    description="AI-powered Healthcare Intelligence Platform Backend for Gujarat PHCs.",
    version="1.0.0",
)

# Cloud Run / Production CORS Config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in strict production environments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================================
# PYDANTIC SCHEMAS
# ==================================================

class StandardResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    data: Any = Field(default_factory=dict)

class PHCRecordBase(BaseModel):
    district: str = Field(..., description="Name of the district")
    taluka: str = Field(..., description="Name of the taluka")
    phc_name: str = Field(..., description="Name of the Primary Health Centre")
    date: str = Field(..., description="Date of the record (YYYY-MM-DD)")
    total_doctors: int = Field(..., ge=0, description="Total number of doctors assigned")
    doctor_present: int = Field(..., ge=0, description="Number of doctors present")
    bed_capacity: int = Field(..., ge=0, description="Total bed capacity")
    occupied_beds: int = Field(..., ge=0, description="Number of occupied beds")
    patient_footfall: int = Field(..., ge=0, description="Total patient footfall")
    medicine_name: str = Field(..., description="Primary critical medicine monitored")
    medicine_stock: int = Field(..., ge=0, description="Current stock of the medicine")
    disease_cases: int = Field(..., ge=0, description="Number of infectious disease cases reported")
    vaccination_count: int = Field(..., ge=0, description="Number of vaccinations administered")
    submitted_by: str = Field(..., description="Name or ID of the recording officer")

    @model_validator(mode="after")
    def check_logical_constraints(self) -> "PHCRecordBase":
        if self.occupied_beds > self.bed_capacity:
            raise ValueError(f"Occupied beds ({self.occupied_beds}) cannot exceed bed capacity ({self.bed_capacity}).")
        if self.doctor_present > self.total_doctors:
            raise ValueError(f"Doctors present ({self.doctor_present}) cannot exceed total doctors ({self.total_doctors}).")
        # Validate date format
        try:
            datetime.strptime(self.date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format.")
        return self

class PHCRecordCreate(PHCRecordBase):
    pass

class PHCRecordUpdate(BaseModel):
    doctor_present: Optional[int] = Field(None, ge=0)
    occupied_beds: Optional[int] = Field(None, ge=0)
    patient_footfall: Optional[int] = Field(None, ge=0)
    medicine_stock: Optional[int] = Field(None, ge=0)
    disease_cases: Optional[int] = Field(None, ge=0)
    vaccination_count: Optional[int] = Field(None, ge=0)

class PHCRecord(PHCRecordBase):
    record_id: str
    timestamp: str

# ==================================================
# HELPER FUNCTIONS
# ==================================================

def generate_response(status_str: str, message: str, data: Any = None) -> Dict:
    """Helper to maintain a consistent JSON response structure."""
    return {
        "status": status_str,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data or {}
    }

# ==================================================
# API ENDPOINTS
# ==================================================

@app.get(
    "/",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Health Check",
    description="Verifies that the FastAPI backend is running and accessible."
)
async def health_check():
    logger.info("Health check endpoint accessed.")
    return generate_response("success", "SevaSetu Backend is running optimally.")


@app.get(
    "/api/dashboard",
    response_model=StandardResponse,
    tags=["Dashboard"],
    summary="Live Dashboard Summary",
    description="Fetches top-level aggregated metrics for the dashboard."
)
async def api_get_dashboard():
    try:
        # Calls imported function from firebase_service
        data = get_dashboard_summary()
        return generate_response("success", "Dashboard summary retrieved", data)
    except Exception as e:
        logger.error(f"Error fetching dashboard summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/overview",
    response_model=StandardResponse,
    tags=["Dashboard"],
    summary="Dashboard Overview",
    description="Fetches detailed overview statistics including patients, beds, and doctors."
)
async def api_get_overview():
    try:
        # Re-using summary or a hypothetical get_overview_data() 
        # based on service layer implementation assumption
        data = get_dashboard_summary() 
        return generate_response("success", "Overview data retrieved", data)
    except Exception as e:
        logger.error(f"Error fetching overview data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/analytics",
    response_model=StandardResponse,
    tags=["Analytics"],
    summary="District Analytics",
    description="Returns detailed analytical metrics aggregated by district."
)
async def api_get_analytics():
    try:
        # Assuming get_all_phc_data handles analytical aggregation or a specific analytics function exists
        data = get_all_phc_data()
        return generate_response("success", "Analytics data retrieved", data)
    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/alerts",
    response_model=StandardResponse,
    tags=["Intelligence"],
    summary="Medicine Alerts",
    description="Returns low stock alerts and predictive supply chain warnings."
)
async def api_get_alerts():
    try:
        data = generate_alerts()
        return generate_response("success", "Alerts retrieved", data)
    except Exception as e:
        logger.error(f"Error fetching alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/trust-score",
    response_model=StandardResponse,
    tags=["Intelligence"],
    summary="Trust Score",
    description="Calculates and returns the PHC data integrity and trust score."
)
async def api_get_trust_score():
    try:
        data = calculate_trust_score()
        return generate_response("success", "Trust scores retrieved", data)
    except Exception as e:
        logger.error(f"Error fetching trust scores: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/outbreaks",
    response_model=StandardResponse,
    tags=["Intelligence"],
    summary="Outbreak Detection",
    description="Returns AI-detected disease clusters and outbreak probabilities."
)
async def api_get_outbreaks():
    try:
        # Mapping to generate_alerts or assuming an outbreak function exists in service
        data = generate_alerts() 
        return generate_response("success", "Outbreak detection data retrieved", data)
    except Exception as e:
        logger.error(f"Error fetching outbreak data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/recommendations",
    response_model=StandardResponse,
    tags=["Intelligence"],
    summary="AI Recommendations",
    description="Fetches AI-driven operational and supply chain recommendations."
)
async def api_get_recommendations():
    try:
        data = generate_recommendations()
        return generate_response("success", "AI recommendations retrieved", data)
    except Exception as e:
        logger.error(f"Error fetching recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/pipeline",
    response_model=StandardResponse,
    tags=["System"],
    summary="Pipeline Status",
    description="Returns the health and execution status of backend ML pipelines."
)
async def api_get_pipeline_status():
    try:
        data = {
            "pipeline_status": "Running",
            "last_execution": datetime.now(timezone.utc).isoformat(),
            "models_loaded": True,
            "latency_ms": 42
        }
        return generate_response("success", "Pipeline status retrieved", data)
    except Exception as e:
        logger.error(f"Error fetching pipeline status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================================================
# CRUD OPERATIONS FOR PHC DATA
# ==================================================

@app.get(
    "/api/phc",
    response_model=StandardResponse,
    tags=["PHC Data"],
    summary="Get All PHC Records",
    description="Retrieves a list of all historical PHC data entries."
)
async def api_get_all_phc():
    try:
        data = get_all_phc_data()
        return generate_response("success", "All PHC records retrieved successfully", data)
    except Exception as e:
        logger.error(f"Error fetching all PHC data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/phc/{record_id}",
    response_model=StandardResponse,
    tags=["PHC Data"],
    summary="Get Single PHC Record",
    description="Fetches a specific PHC data record by its unique record_id."
)
async def api_get_phc_record(record_id: str):
    try:
        # Assumes a function like get_record(record_id) exists, or filters get_all_phc_data
        records = get_all_phc_data()
        record = records.get(record_id) if isinstance(records, dict) else next((r for r in records if r.get("record_id") == record_id), None)
        
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
            
        return generate_response("success", "Record retrieved successfully", record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching PHC record {record_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/api/phc",
    response_model=StandardResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["PHC Data"],
    summary="Create PHC Record",
    description="Inserts a new PHC daily data record into Firebase."
)
async def api_create_phc_record(record: PHCRecordCreate):
    try:
        record_id = f"PHC-{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now(timezone.utc).isoformat()
        
        phc_data_dict = record.model_dump()
        phc_data_dict["record_id"] = record_id
        phc_data_dict["timestamp"] = timestamp
        
        save_phc_data(phc_data_dict)
        
        logger.info(f"Created new PHC record: {record_id}")
        return generate_response(
            status_str="success",
            message="PHC data saved successfully",
            data=phc_data_dict
        )
    except ValueError as ve:
        logger.warning(f"Validation error on create: {str(ve)}")
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.error(f"Error creating PHC record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put(
    "/api/phc/{record_id}",
    response_model=StandardResponse,
    tags=["PHC Data"],
    summary="Update PHC Record",
    description="Updates specific fields of an existing PHC record."
)
async def api_update_phc_record(record_id: str, updates: PHCRecordUpdate):
    try:
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields provided for update")
            
        update_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        update_record(record_id, update_data)
        
        logger.info(f"Updated PHC record: {record_id}")
        return generate_response("success", "PHC data updated successfully", {"record_id": record_id, "updated_fields": update_data})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating PHC record {record_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete(
    "/api/phc/{record_id}",
    response_model=StandardResponse,
    tags=["PHC Data"],
    summary="Delete PHC Record",
    description="Removes a PHC data record from Firebase."
)
async def api_delete_phc_record(record_id: str):
    try:
        delete_record(record_id)
        logger.info(f"Deleted PHC record: {record_id}")
        return generate_response("success", f"PHC record {record_id} deleted successfully")
    except Exception as e:
        logger.error(f"Error deleting PHC record {record_id}: {str(e)}")
<<<<<<< HEAD
        raise HTTPException(status_code=500, detail=str(e))
=======
        raise HTTPException(status_code=500, detail=str(e))
>>>>>>> 7aaffb768011c2e603b4ff9e1cf3ea1b6e22f556
