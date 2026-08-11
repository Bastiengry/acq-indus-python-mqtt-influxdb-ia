import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sklearn.ensemble import IsolationForest
from influxdb_client import InfluxDBClient
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INFLUX_URL = os.getenv("INFLUXDB_URL", "http://acq-indus-influxdb:8086")
INFLUX_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUX_ORG = os.getenv("INFLUXDB_ORG", "bg_soft")
INFLUX_BUCKET = os.getenv("INFLUXDB_BUCKET", "fan_telemetry")

influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)


def get_recent_data(fan_id: str, minutes: int = 1440) -> pd.DataFrame:
    """Récupère l'ensemble des points récents sous forme d'une série temporelle unique."""
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
        
        # Formatage du tableau complet des données pour le tracer de la courbe
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

        # Évaluation de l'IA
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
            
            # 1. Moyennes et écarts-types historiques
            means = features.mean()
            stds = features.std().replace(0, 1e-6) # Évite la division par zéro
            
            # 2. Calcul de la déviation (Z-Score) pour le dernier point
            last_point_series = last_point.iloc[0]
            z_scores = ((last_point_series - means) / stds).abs()
            
            # 3. La colonne responsable est celle avec le Z-Score le plus élevé
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


@app.on_event("shutdown")
def shutdown_event():
    influx_client.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)