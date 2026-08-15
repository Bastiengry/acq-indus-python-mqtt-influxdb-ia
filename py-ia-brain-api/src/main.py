import os
import logging
import asyncio
from contextlib import asynccontextmanager
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sklearn.ensemble import IsolationForest
from influxdb_client import InfluxDBClient
from neo4j import GraphDatabase
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

# --- Configuration des Logs ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_hypervisor_api")

# --- Configuration InfluxDB ---
INFLUX_URL = os.getenv("INFLUXDB_URL", "http://acq-indus-influxdb:8086")
INFLUX_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUX_ORG = os.getenv("INFLUXDB_ORG", "bg_soft")
INFLUX_BUCKET = os.getenv("INFLUXDB_BUCKET", "fan_telemetry")

# --- Configuration Neo4j ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://acq-indus-neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

# Clients de base de données
influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


class ChatMessage(BaseModel):
    message: str


def run_sync_logic():
    """Logique d'extraction InfluxDB et injection Neo4j (exécutée hors thread principal)."""
    logger.info("--> [SYNC] Interrogation d'InfluxDB pour mise à jour du graphe...")
    
    # Requête Flux : conservation des tags fan_id, location et du field
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -30d)
      |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer")
      |> keep(columns: ["fan_id", "location", "_field"])
      |> group(columns: ["fan_id", "location", "_field"])
      |> distinct(column: "_field")
    '''
    try:
        query_api = influx_client.query_api()
        tables = query_api.query(query)
        
        # Structure : { fan_id: {"sensors": set(), "location": str} }
        topology = {}
        for table in tables:
            for record in table.records:
                fan_id = record.values.get("fan_id")
                location = record.values.get("location") or "Unknown"
                field = record.get_value()
                
                if fan_id and field:
                    if fan_id not in topology:
                        topology[fan_id] = {"sensors": set(), "location": location}
                    topology[fan_id]["sensors"].add(field)

        if not topology:
            logger.warning("--> [SYNC] Aucune donnée avec le tag 'fan_id' n'a été trouvée dans InfluxDB.")
            return

        cypher_query = """
        MERGE (t:Tunnel {id: $location})
        ON CREATE SET t.name = $location
        
        MERGE (f:Fan {id: $fan_id})
        ON CREATE SET f.name = $fan_id
        MERGE (t)-[:HAS_EQUIPMENT]->(f)
        MERGE (f)-[:LOCATED_IN]->(t)

        WITH f
        UNWIND $sensors AS sensor_type
        MERGE (s:Sensor {id: $fan_id + "_" + toUpper(sensor_type)})
        ON CREATE SET s.type = sensor_type
        MERGE (f)-[:HAS_SENSOR]->(s)
        MERGE (s)-[:MONITORS]->(f)
        """

        with neo4j_driver.session() as session:
            for fan_id, data in topology.items():
                session.run(
                    cypher_query, 
                    fan_id=fan_id, 
                    sensors=list(data["sensors"]), 
                    location=data["location"]
                )

        logger.info(f"--> [SYNC SUCCESS] Topologie Neo4j mise à jour pour : {list(topology.keys())}")

    except Exception as e:
        logger.error(f"--> [SYNC ERROR] Échec lors de la synchronisation : {e}")


async def sync_influx_to_neo4j():
    """Wrapper asynchrone non-bloquant pour l'Event Loop."""
    await asyncio.to_thread(run_sync_logic)


# Gestion du cycle de vie FastAPI (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialisation du scheduler dans l'event loop active de FastAPI
    scheduler = AsyncIOScheduler()
    
    # 1. Synchronisation initiale au démarrage
    await sync_influx_to_neo4j()
    
    # 2. Planification récurrente toutes les 20 secondes
    scheduler.add_job(sync_influx_to_neo4j, 'interval', seconds=20)
    scheduler.start()
    logger.info("--> [SCHEDULER] Planificateur démarré (fréquence: 20 secondes)")
    
    yield
    
    # 3. Arrêt propre des ressources
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


def get_recent_data(fan_id: str, minutes: int = 1440) -> pd.DataFrame:
    """Récupère les points récents sous forme de série temporelle."""
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -{minutes}m)
      |> filter(fn: (r) => r["fan_id"] == "{fan_id}")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> group()
      |> sort(columns: ["_time"])
      |> tail(n: 300)
    '''
    query_api = influx_client.query_api()
    return query_api.query_data_frame(query)


@app.post("/sync-topology")
async def trigger_manual_sync():
    """Endpoint déclenchant la synchronisation manuelle InfluxDB -> Neo4j."""
    await sync_influx_to_neo4j()
    return {"status": "success", "message": "Synchronisation de la topologie effectuée."}


@app.get("/data-with-anomaly-detection/{fan_id}")
async def get_data_and_detect_anomaly(fan_id: str):
    try:
        df = get_recent_data(fan_id, minutes=1440)
        
        if df is None or df.empty:
            return {
                "fan_id": fan_id,
                "status": "no_data",
                "health_status": "UNKNOWN",
                "faulty_feature": None,
                "points_count": 0,
                "data": []
            }

        required_cols = ['vibration', 'temperature', 'current']
        available_cols = [c for c in required_cols if c in df.columns]
        
        time_col = '_time' if '_time' in df.columns else 'time'
        records = []
        for _, row in df.iterrows():
            record = {"timestamp": str(row[time_col])}
            for col in available_cols:
                record[col] = float(row[col]) if pd.notnull(row[col]) else None
            records.append(record)

        features = df[available_cols].dropna()
        last_row = df.iloc[-1]

        response = {
            "fan_id": fan_id,
            "status": "ok",
            "last_vibration": float(last_row['vibration']) if 'vibration' in last_row and pd.notnull(last_row['vibration']) else None,
            "last_temperature": float(last_row['temperature']) if 'temperature' in last_row and pd.notnull(last_row['temperature']) else None,
            "last_current": float(last_row['current']) if 'current' in last_row and pd.notnull(last_row['current']) else None,
            "timestamp": str(last_row[time_col]),
            "points_count": len(features),
            "data": records
        }

        MIN_POINTS_FOR_AI = 10
        if len(features) < MIN_POINTS_FOR_AI:
            response["health_status"] = "WARMUP"
            response["faulty_feature"] = None
            response["ai_message"] = f"Apprentissage en cours ({len(features)}/{MIN_POINTS_FOR_AI} points)"
            return response

        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(features)
        
        last_point = features.iloc[[-1]]
        prediction = model.predict(last_point)[0]
        
        if prediction == -1:
            health_status = "CRITICAL"
            historical_features = features.iloc[:-1]
            means = historical_features.mean()
            stds = historical_features.std().replace(0, 1e-6)
            
            last_point_series = last_point.iloc[0]
            z_scores = ((last_point_series - means) / stds).abs()
            
            faulty_feature = str(z_scores.idxmax())
            fault_value = float(last_point_series[faulty_feature])
            
            ai_message = f"Anomalie détectée sur {faulty_feature.upper()} ({fault_value:.2f})"
        else:
            health_status = "OK"
            faulty_feature = None
            ai_message = "Système nominal"

        response["health_status"] = health_status
        response["faulty_feature"] = faulty_feature
        response["ai_message"] = ai_message
        
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/context/{fan_id}")
def get_fan_context(fan_id: str):
    query = """
    MATCH (f:Fan {id: $fan_id})-[:LOCATED_IN]->(t:Tunnel)
    OPTIONAL MATCH (f)<-[:MONITORS]-(s:Sensor)
    RETURN t.name as tunnel, f.name as name, collect(s.id) as sensors
    """
    try:
        with neo4j_driver.session() as session:
            result = session.run(query, fan_id=fan_id).single()
            if not result:
                raise HTTPException(status_code=404, detail="Ventilateur non trouvé dans le graphe")
            return dict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_bot(payload: ChatMessage):
    user_msg = payload.message.lower().strip()
    
    try:
        # Intention 1 : Demande de liste des capteurs
        if "capteur" in user_msg and ("liste" in user_msg or "tous" in user_msg or "quelles" in user_msg or "quels" in user_msg):
            query = """
            MATCH (s:Sensor)-[:MONITORS]->(f:Fan)
            RETURN s.id as sensor_id, s.type as type, f.id as fan_id
            ORDER BY f.id, s.type
            """
            with neo4j_driver.session() as session:
                results = session.run(query).data()
                
            if not results:
                return {"reply": "Aucun capteur n'a été trouvé dans le graphe."}
                
            formatted_list = [
                f"• **{r['sensor_id']}** (Type: `{r['type']}`) — Surveille: `{r['fan_id']}`"
                for r in results
            ]
            reply_text = f"Voici la liste des **{len(results)} capteurs** détectés dans la topologie :\n\n" + "\n".join(formatted_list)
            return {"reply": reply_text}

        # Intention 2 : Demande de liste des ventilateurs / équipements
        elif "ventilateur" in user_msg or "fan" in user_msg or "équipement" in user_msg:
            query = """
            MATCH (f:Fan)-[:LOCATED_IN]->(t:Tunnel)
            OPTIONAL MATCH (f)-[:HAS_SENSOR]->(s:Sensor)
            RETURN f.id as fan_id, t.name as tunnel, count(s) as nb_sensors
            ORDER BY f.id
            """
            with neo4j_driver.session() as session:
                results = session.run(query).data()
                
            if not results:
                return {"reply": "Aucun ventilateur trouvé."}
                
            formatted_list = [
                f"• **{r['fan_id']}** dans le tunnel **{r['tunnel']}** ({r['nb_sensors']} capteurs associés)"
                for r in results
            ]
            return {"reply": "Voici les ventilateurs enregistrés :\n\n" + "\n".join(formatted_list)}

        # Intention 3 : Demande sur les tunnels / localisations
        elif "tunnel" in user_msg or "localisation" in user_msg:
            query = """
            MATCH (t:Tunnel)<-[:LOCATED_IN]-(f:Fan)
            RETURN t.name as tunnel, collect(f.id) as fans
            """
            with neo4j_driver.session() as session:
                results = session.run(query).data()
                
            formatted_list = [
                f"• **{r['tunnel']}** : {', '.join(r['fans'])}"
                for r in results
            ]
            return {"reply": "Répartition des équipements par tunnel :\n\n" + "\n".join(formatted_list)}

        # Fallback si l'intention n'est pas reconnue
        else:
            return {
                "reply": (
                    "Je suis l'assistant de supervision du réseau. Voici quelques exemples de questions que vous pouvez me poser :\n\n"
                    "- *\"Donne-moi la liste des capteurs\"*\n"
                    "- *\"Quels sont les ventilateurs ?\"*\n"
                    "- *\"Liste des tunnels\"*"
                )
            }

    except Exception as e:
        logger.error(f"Erreur Chatbot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)