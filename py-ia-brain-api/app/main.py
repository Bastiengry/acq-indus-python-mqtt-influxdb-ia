import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import uvicorn

from app.core.config import influx_client, neo4j_driver, logger
from app.services.sync_service import SyncService
from app.services.fan_machine_learning_service import FanMachineLearningService
from app.services.fan_service import FanService
from app.controllers import telemetry_controller, topology_controller, chat_controller

sync_service = SyncService()
fan_machine_learning_service = FanMachineLearningService()
fan_service = FanService()


# Fonctions wrappers asynchrones propres pour le Scheduler
async def scheduled_sync_neo4j():
    await asyncio.to_thread(sync_service.sync_influx_to_neo4j)

async def scheduled_ml_update():
    await asyncio.to_thread(fan_machine_learning_service.update_last_predictions)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lancement de la synchronisation initiale de Neo4j dans un thread dédié
    await asyncio.to_thread(sync_service.sync_influx_to_neo4j)

    # Configuration du Scheduler
    scheduler = AsyncIOScheduler()

    # Synchronisation Neo4j (toutes les 20s)
    scheduler.add_job(
        scheduled_sync_neo4j,
        'interval',
        seconds=20
    )
    logger.info("--> [SCHEDULER] Planificateur configuré pour mise à jour de Neo4j (20s)")

    # Détection, auto-entraînement à la volée et prédictions ML (toutes les 3s)
    scheduler.add_job(
        scheduled_ml_update,
        'interval',
        seconds=3
    )
    logger.info("--> [SCHEDULER] Planificateur configuré pour prédictions ML & Auto-entraînement (3s)")

    scheduler.start()

    yield

    # Clean-up à l'arrêt
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