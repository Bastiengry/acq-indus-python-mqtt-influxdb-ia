from fastapi import FastAPI
import pandas as pd
from sklearn.ensemble import IsolationForest
from influxdb_client import InfluxDBClient
import uvicorn
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configuration du Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En prod, mets l'URL de ton front, ici "*" autorise tout pour le dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration InfluxDB
url = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
token = os.getenv("INFLUXDB_TOKEN")
org = os.getenv("INFLUXDB_ORG")
bucket = os.getenv("INFLUXDB_BUCKET")
aiApiFilterAddr = os.getenv("AI_API_FILTER_ADDR")
aiApiPort = os.getenv("AI_API_PORT")

model = IsolationForest(contamination=0.1)
is_model_trained = False

def get_recent_data(fan_id: str, minutes: int = 10):
    client = InfluxDBClient(url=url, token=token, org=org)
    query_api = client.query_api()
    
    # Correction de la requête Flux : ajout des pipes "|>" et des parenthèses/guillemets
    # On limite à 200 points pour ne pas saturer la RAM
    query = f'''
    from(bucket: "{bucket}")
      |> range(start: -{minutes}m)
      |> filter(fn: (r) => r["fan_id"] == "{fan_id}")
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> tail(n: 200)
    '''
    df = query_api.query_data_frame(query)
    return df

@app.get("/health/{fan_id}") # Correction du chemin (slash et accolades)
async def check_fan_health(fan_id: str):
    global is_model_trained
    
    # 1. Récupération des données
    df = get_recent_data(fan_id)
    
    if df is None or df.empty:
        return {"status": "no_data"} # Ajout des guillemets

    # 2. Préparation des features pour l'IA
    features = df[['vibration', 'temperature', 'current']]
    
    # 3. Entraînement/Inférence
    # --- OPTIMISATION IA ---
    # On n'entraîne que si nécessaire ou au premier appel
    if not is_model_trained:
        model.fit(features)
        is_model_trained = True
    
    # Prédiction sur le dernier point reçu
    last_point = features.iloc[[-1]]
    prediction = model.predict(last_point)[0]
    
    # Correction des chaînes de caractères
    health_score = "CRITICAL" if prediction == -1 else "OK"
    
    # Correction de la structure du dictionnaire de retour
    return {
        "fan_id": fan_id,
        "health_status": health_score,
        "last_vibration": float(last_point['vibration'].values[0]),
        "timestamp": str(df.iloc[-1]['_time'])
    }

if __name__ == "__main__": # Correction des guillemets et ajout des deux points
    uvicorn.run(app, host="0.0.0.0", port=8000)