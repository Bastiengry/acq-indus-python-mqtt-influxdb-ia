from fastapi import APIRouter, HTTPException
from app.services.anomaly_service import AnomalyService

router = APIRouter()
anomaly_service = AnomalyService()

@router.get("/data-with-anomaly-detection/{fan_id}")
async def get_data_and_detect_anomaly(fan_id: str):
    try:
        return anomaly_service.analyze_fan(fan_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))