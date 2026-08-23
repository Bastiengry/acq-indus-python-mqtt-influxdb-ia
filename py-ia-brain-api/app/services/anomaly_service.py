import pandas as pd
from sklearn.ensemble import IsolationForest
from app.repositories.influx_repo import InfluxRepository

class AnomalyService:
    def __init__(self):
        self.influx_repo = InfluxRepository()

    def analyze_fan(self, fan_id: str):
        df = self.influx_repo.get_recent_data(fan_id, minutes=1440)
        
        if df is None or df.empty:
            return {
                "fan_id": fan_id, "status": "no_data", "health_status": "UNKNOWN",
                "faulty_feature": None, "points_count": 0, "data": []
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

        MIN_POINTS = 10
        if len(features) < MIN_POINTS:
            response["health_status"] = "WARMUP"
            response["faulty_feature"] = None
            response["ai_message"] = f"Apprentissage en cours ({len(features)}/{MIN_POINTS} points)"
            return response

        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(features)
        
        last_point = features.iloc[[-1]]
        if model.predict(last_point)[0] == -1:
            health_status = "CRITICAL"
            historical = features.iloc[:-1]
            stds = historical.std().replace(0, 1e-6)
            z_scores = ((last_point.iloc[0] - historical.mean()) / stds).abs()
            
            faulty_feature = str(z_scores.idxmax())
            fault_val = float(last_point.iloc[0][faulty_feature])
            ai_message = f"Anomalie détectée sur {faulty_feature.upper()} ({fault_val:.2f})"
        else:
            health_status = "OK"
            faulty_feature = None
            ai_message = "Système nominal"

        response.update({
            "health_status": health_status,
            "faulty_feature": faulty_feature,
            "ai_message": ai_message
        })
        return response