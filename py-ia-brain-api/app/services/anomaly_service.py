import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from app.repositories.influx_repo import InfluxRepository

class AnomalyService:
    def __init__(self, model_dir: str = "models"):
        self.influx_repo = InfluxRepository()
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        self._models_cache = {}

    def _get_model_path(self, fan_id: str) -> str:
        return os.path.join(self.model_dir, f"isolation_forest_{fan_id}.joblib")

    def _load_model(self, fan_id: str):
        if fan_id in self._models_cache:
            return self._models_cache[fan_id]

        model_path = self._get_model_path(fan_id)
        if os.path.exists(model_path):
            model = joblib.load(model_path)
            self._models_cache[fan_id] = model
            return model
        return None

    def train_fan_model(self, fan_id: str, n_samples: int = 1000) -> bool:
        """Méthode explicite pour générer le modèle de référence sain."""
        np.random.seed(42)
        vibrations = 2.5 + np.random.normal(0, 0.1, n_samples)
        temperatures = 45.0 + np.random.normal(0, 0.5, n_samples)
        currents = 12.0 + np.random.normal(0, 0.2, n_samples)

        features = pd.DataFrame({
            'vibration': vibrations,
            'temperature': temperatures,
            'current': currents
        })

        model = IsolationForest(contamination=0.01, random_state=42)
        model.fit(features)

        model_path = self._get_model_path(fan_id)
        joblib.dump(model, model_path)
        self._models_cache[fan_id] = model
        return True

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

        # 1. Tentative de chargement du modèle
        model = self._load_model(fan_id)

        # 2. Pas de modèle = REFUS de prédire (pas d'entraînement caché)
        if model is None:
            response.update({
                "health_status": "UNTRAINED",
                "faulty_feature": None,
                "ai_message": "Modèle non entraîné. Veuillez exécuter la phase d'apprentissage."
            })
            return response

        # 3. Inférence stricte sur le modèle existant
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