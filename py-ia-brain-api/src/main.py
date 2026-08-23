import os
import json
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
import ollama

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

# --- Configuration Ollama ---
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://acq-indus-ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

# Clients de base de données
influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
client_ollama = ollama.Client(host=OLLAMA_HOST)


class ChatMessage(BaseModel):
    message: str


def run_sync_logic():
    """Logique d'extraction InfluxDB et injection Neo4j (exécutée hors thread principal)."""
    logger.info("--> [SYNC] Interrogation d'InfluxDB pour mise à jour du graphe...")
    
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    await sync_influx_to_neo4j()
    scheduler.add_job(sync_influx_to_neo4j, 'interval', seconds=20)
    scheduler.start()
    logger.info("--> [SCHEDULER] Planificateur démarré (fréquence: 20 secondes)")
    
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
    result = query_api.query_data_frame(query)

    if isinstance(result, list):
        if not result:
            return pd.DataFrame()
        return pd.concat(result, ignore_index=True)
    return result


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


# --- Outils d'aide pour le Chatbot LLM ---

def tool_get_network_topology() -> str:
    """Interroge Neo4j pour la topologie globale."""
    query = """
    MATCH (t:Tunnel)<-[:LOCATED_IN]-(f:Fan)
    OPTIONAL MATCH (f)-[:HAS_SENSOR]->(s:Sensor)
    RETURN t.name as tunnel, f.id as fan_id, collect(s.id) as sensors
    """
    try:
        with neo4j_driver.session() as session:
            results = session.run(query).data()
            return json.dumps(results)
    except Exception as e:
        return f"Erreur Neo4j: {str(e)}"


def tool_get_sensor_list() -> str:
    """Interroge Neo4j pour la liste des capteurs."""
    query = """
    MATCH (s:Sensor)-[:MONITORS]->(f:Fan)
    RETURN s.id as sensor_id, s.type as type, f.id as fan_id
    ORDER BY f.id, s.type
    """
    try:
        with neo4j_driver.session() as session:
            results = session.run(query).data()
            return json.dumps(results)
    except Exception as e:
        return f"Erreur Neo4j: {str(e)}"


def resolve_fan_and_sensor(target_id: str):
    """Résout le fan_id et extrait le type de capteur si renseigné."""
    target_clean = target_id.strip()
    
    # Recherche dans Neo4j si target_clean est un Sensor
    query_sensor = "MATCH (s:Sensor {id: $id})-[:MONITORS]->(f:Fan) RETURN f.id as fan_id, s.type as sensor_type"
    with neo4j_driver.session() as session:
        res = session.run(query_sensor, id=target_clean).single()
        if res:
            return res["fan_id"], res["sensor_type"].lower()
            
    # Extraction manuelle si suffixe d'un sous-type (_TEMPERATURE, _VIBRATION, _CURRENT)
    for metric in ["temperature", "vibration", "current"]:
        if target_clean.lower().endswith(f"_{metric}"):
            fan_part = target_clean[:-len(metric)-1]
            return fan_part, metric
            
    return target_clean, None


async def tool_check_eqp_or_sensor_health(target_id: str) -> str:
    """Vérifie la santé d'un équipement ou filtre par capteur spécifique."""
    try:
        fan_id, sensor_type = resolve_fan_and_sensor(target_id)
        res = await get_data_and_detect_anomaly(fan_id)

        # Si un capteur spécifique était visé, on ne renvoie que la métrique demandée
        if sensor_type:
            metric_key = f"last_{sensor_type}"
            val = res.get(metric_key)
            return json.dumps({
                "sensor_id": target_id,
                "fan_id": fan_id,
                "sensor_type": sensor_type,
                "value": val,
                "timestamp": res.get("timestamp"),
                "health_status": res.get("health_status"),
                "is_anomalous": (res.get("faulty_feature") == sensor_type)
            })

        return json.dumps(res)
    except Exception as e:
        return f"Erreur analyse santé pour '{target_id}': {str(e)}"


OLLAMA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_network_topology",
            "description": "Obtenir la structure globale du réseau (tunnels et équipements associés). À utiliser pour la vue d'ensemble.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_sensor_list",
            "description": "Obtenir la liste détaillée de TOUS les capteurs avec leur type et l'équipement qu'ils surveillent.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_eqp_or_sensor_health",
            "description": "Obtenir l'état de santé et les valeurs d'un équipement complet ou d'un capteur spécifique.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_id": {
                        "type": "string",
                        "description": "L'identifiant exact de l'équipement (ex: FAN_01) ou du capteur (ex: FAN_01_TEMPERATURE)."
                    }
                },
                "required": ["target_id"]
            }
        }
    }
]


@app.post("/chat")
async def chat_bot(payload: ChatMessage):
    user_msg = payload.message.strip()
    
    messages = [
        {
            "role": "system",
            "content": (
                "Tu es un assistant IA de supervision industrielle. "
                "Tu as accès à des outils pour lire le graphe Neo4j et analyser les anomalies télémétriques. "
                "Si l'utilisateur demande des informations sur un capteur précis (ex: FAN_04_TEMPERATURE), "
                "donne uniquement la valeur et l'état de ce capteur sans détailler l'ensemble des autres capteurs. "
                "Sois précis, utile et réponds toujours en français."
            )
        },
        {"role": "user", "content": user_msg}
    ]

    try:
        response = await asyncio.to_thread(
            client_ollama.chat,
            model=OLLAMA_MODEL,
            messages=messages,
            tools=OLLAMA_TOOLS
        )

        message = response['message']

        while message.get('tool_calls'):
            messages.append(message)
            
            for tool in message['tool_calls']:
                func_name = tool['function']['name']
                raw_args = tool['function']['arguments']
                
                # Sécurité si les arguments sont sérialisés en JSON string
                arguments = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                
                if func_name == "get_network_topology":
                    tool_result = await asyncio.to_thread(tool_get_network_topology)
                elif func_name == "get_sensor_list":
                    tool_result = await asyncio.to_thread(tool_get_sensor_list)
                elif func_name == "check_eqp_or_sensor_health":
                    target = arguments.get("target_id") or arguments.get("fan_id", "")
                    tool_result = await tool_check_eqp_or_sensor_health(target)
                else:
                    tool_result = "Outil inconnu"

                messages.append({
                    "role": "tool",
                    "content": str(tool_result)
                })

            # Prochain tour avec le LLM pour vérifier s'il demande d'autres outils ou conclut
            response = await asyncio.to_thread(
                client_ollama.chat,
                model=OLLAMA_MODEL,
                messages=messages,
                tools=OLLAMA_TOOLS
            )
            message = response['message']

        return {"reply": message['content']}

    except Exception as e:
        logger.error(f"Erreur Chatbot LLM: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur du service LLM: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)