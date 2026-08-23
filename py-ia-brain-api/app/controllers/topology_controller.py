from fastapi import APIRouter, HTTPException
from app.services.sync_service import SyncService
from app.repositories.neo4j_repo import Neo4jRepository

router = APIRouter()
sync_service = SyncService()
neo4j_repo = Neo4jRepository()

@router.post("/sync-topology")
async def trigger_manual_sync():
    await sync_service.sync_influx_to_neo4j()
    return {"status": "success", "message": "Synchronisation de la topologie effectuée."}

@router.get("/context/{fan_id}")
def get_fan_context(fan_id: str):
    try:
        ctx = neo4j_repo.get_fan_context(fan_id)
        if not ctx:
            raise HTTPException(status_code=404, detail="Ventilateur non trouvé")
        return ctx
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))