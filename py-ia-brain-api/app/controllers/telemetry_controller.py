from fastapi import APIRouter, HTTPException
from app.services.fan_service import FanService
from app.services.fan_machine_learning_service import FanMachineLearningService

router = APIRouter()
fan_service = FanService()
fan_machine_learning_service = FanMachineLearningService()

@router.get("/last-data/{fan_id}")
async def get_data(fan_id: str):
    try:
        return fan_service.read_data(fan_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/last-prediction/{fan_id}")
async def get_last_prediction(fan_id: str):
    try:
        return fan_machine_learning_service.read_last_prediction(fan_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))