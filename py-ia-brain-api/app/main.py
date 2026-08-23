from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import uvicorn

from app.core.config import influx_client, neo4j_driver, logger
from app.services.sync_service import SyncService
from app.controllers import telemetry_controller, topology_controller, chat_controller

sync_service = SyncService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    await sync_service.sync_influx_to_neo4j()
    scheduler.add_job(sync_service.sync_influx_to_neo4j, 'interval', seconds=20)
    scheduler.start()
    logger.info("--> [SCHEDULER] Planificateur démarré (20s)")
    
    yield
    
    scheduler.shutdown()
    influx_client.close()
    neo4j_driver.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes
app.include_router(telemetry_controller.router)
app.include_router(topology_controller.router)
app.include_router(chat_controller.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)