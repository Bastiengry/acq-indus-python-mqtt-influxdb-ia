import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from app.repositories.influx_repo import InfluxRepository

class AnomalyService:
    def __init__(self, model_dir: str = "models"):
        self.influx_repo = InfluxRepository()
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        self._models_cache = {}

    def _get_model_paths(self, fan_id: str):
        """Retourne les chemins des fichiers de modèles pour un ventilateur."""
        iso_path = os.path.join(self.model_dir, f"iso_{fan_id}.joblib")
        clf_path = os.path.join(self.model_dir, f"clf_{fan_id}.joblib")
        return iso_path, clf_path

    def _load_model(self, model_path: str, cache_key: str):
        """Charge un modèle depuis le cache mémoire ou le disque."""
        if cache_key in self._models_cache:
            return self._models_cache[cache_key]

        if os.path.exists(model_path):
            model = joblib.load(model_path)
            self._models_cache[cache_key] = model
            return model
        return None

    # =========================================================================
    # 1. ENTRAÎNEMENT : ISOLATION FOREST (Détection d'Anomalie)
    # =========================================================================
    def train_isolation_forest(self, fan_id: str, n_samples: int = 1000) -> bool:
        """Génère le modèle de référence pour les données saines."""
        np.random.seed(42)
        vibrations = 2.5 + np.random.normal(0, 0.1, n_samples)
        temperatures = 45.0 + np.random.normal(0, 0.5, n_samples)
        currents = 12.0 + np.random.normal(0, 0.2, n_samples)

        features = pd.DataFrame({
            'vibration': vibrations,
            'temperature': temperatures,
            'current': currents
        })

        iso_model = IsolationForest(contamination=0.01, random_state=42)
        iso_model.fit(features)

        iso_path, _ = self._get_model_paths(fan_id)
        joblib.dump(iso_model, iso_path)
        self._models_cache[f"iso_{fan_id}"] = iso_model
        return True

    # =========================================================================
    # 2. ENTRAÎNEMENT : RANDOM FOREST (Classification de la Panne)
    # =========================================================================
    def train_fault_classifier(self, fan_id: str, n_samples_per_class: int = 300) -> bool:
        """Génère un dataset d'incidents étiquetés et entraîne le classifieur."""
        np.random.seed(42)

        # Classe 0 : NOMINAL
        vib_0 = 2.5 + np.random.normal(0, 0.1, n_samples_per_class)
        temp_0 = 45.0 + np.random.normal(0, 0.5, n_samples_per_class)
        curr_0 = 12.0 + np.random.normal(0, 0.2, n_samples_per_class)

        # Classe 1 : MECHANICAL_WEAR (Vibration élevée)
        vib_1 = 2.5 + np.random.uniform(1.0, 3.0, n_samples_per_class)
        temp_1 = 45.0 + np.random.normal(0, 0.5, n_samples_per_class)
        curr_1 = 12.0 + np.random.normal(0, 0.2, n_samples_per_class)

        # Classe 2 : MOTOR_OVERHEAT (Température + Courant élevés)
        vib_2 = 2.5 + np.random.normal(0, 0.1, n_samples_per_class)
        temp_2 = 45.0 + np.random.uniform(10.0, 25.0, n_samples_per_class)
        curr_2 = 12.0 + np.random.uniform(2.0, 5.0, n_samples_per_class)

        X_train = np.vstack([
            np.column_stack([vib_0, temp_0, curr_0]),
            np.column_stack([vib_1, temp_1, curr_1]),
            np.column_stack([vib_2, temp_2, curr_2])
        ])
        y_train = np.array(
            [0] * n_samples_per_class + 
            [1] * n_samples_per_class + 
            [2] * n_samples_per_class
        )

        clf_model = RandomForestClassifier(n_estimators=20, random_state=42)
        clf_model.fit(X_train, y_train)

        _, clf_path = self._get_model_paths(fan_id)
        joblib.dump(clf_model, clf_path)
        self._models_cache[f"clf_{fan_id}"] = clf_model
        return True

    # =========================================================================
    # 3. INFÉRENCE COMPLÈTE (Iso Forest + Z-Score + Random Forest)
    # =========================================================================
    def analyze_fan(self, fan_id: str):
        df = self.influx_repo.get_recent_data(fan_id, minutes=1440)
        
        if df is None or df.empty:
            return {
                "fan_id": fan_id, "status": "no_data", "health_status": "UNKNOWN",
                "faulty_feature": None, "fault_label": None, "points_count": 0, "data": []
            }

        required_cols = ['vibration', 'temperature', 'current']
        available_cols = [c for c in required_cols if c in df.columns]
        time_col = '_time' if '_time' in df.columns else 'time'
        
        records = [
            {
                "timestamp": str(row[time_col]),
                **{col: (float(row[col]) if pd.notnull(row[col]) else None) for col in available_cols}
            }
            for _, row in df.iterrows()
        ]

        features = df[available_cols].dropna()
        if features.empty:
            return {
                "fan_id": fan_id, "status": "no_data", "health_status": "UNKNOWN",
                "faulty_feature": None, "fault_label": None, "points_count": 0, "data": records
            }
            
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

        # 1. Chargement des modèles
        iso_path, clf_path = self._get_model_paths(fan_id)
        iso_model = self._load_model(iso_path, f"iso_{fan_id}")
        clf_model = self._load_model(clf_path, f"clf_{fan_id}")

        # 2. Blocage si les modèles sont absents
        if iso_model is None or clf_model is None:
            response.update({
                "health_status": "UNTRAINED",
                "faulty_feature": None,
                "fault_label": None,
                "ai_message": "Modèles non entraînés. Veuillez exécuter la phase d'apprentissage."
            })
            return response

        # 3. Inférence ML & Calcul Z-Score
        last_point = features.iloc[[-1]]

        if iso_model.predict(last_point)[0] == -1:
            health_status = "CRITICAL"
            
            # --- Z-SCORE (Identification de la variable déviante) ---
            historical = features.iloc[:-1] if len(features) > 1 else features
            stds = historical.std().replace(0, 1e-6)
            z_scores = ((last_point.iloc[0] - historical.mean()) / stds).abs()
            faulty_feature = str(z_scores.idxmax())
            
            # --- RANDOM FOREST (Diagnostic métier) ---
            fault_code = clf_model.predict(last_point)[0]
            labels = {
                1: "Usure mécanique / Désalignement",
                2: "Surchauffe Moteur / Surcharge électrique"
            }
            fault_label = labels.get(fault_code, "Anomalie non classifiée")

            fault_val = float(last_point.iloc[0][faulty_feature])
            ai_message = f"Anomalie sur {faulty_feature.upper()} ({fault_val:.2f}) - Diagnostics : {fault_label}"
        else:
            health_status = "OK"
            faulty_feature = None
            fault_label = None
            ai_message = "Système nominal"

        response.update({
            "health_status": health_status,
            "faulty_feature": faulty_feature,
            "fault_label": fault_label,
            "ai_message": ai_message
        })
        return response