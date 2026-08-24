import os
import logging
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from app.repositories.influx_repo import InfluxRepository

logger = logging.getLogger(__name__)


class FanMachineLearningService:
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

    def train_isolation_forest(self, fan_id: str, n_samples: int = 1000) -> bool:
        """Génère le modèle de référence pour les données saines."""
        rng = np.random.default_rng(42)

        features = pd.DataFrame({
            'vibration': 2.5 + rng.normal(0, 0.1, n_samples),
            'temperature': 45.0 + rng.normal(0, 0.5, n_samples),
            'current': 12.0 + rng.normal(0, 0.2, n_samples)
        })

        iso_model = IsolationForest(contamination=0.01, random_state=42)
        iso_model.fit(features)

        iso_path, _ = self._get_model_paths(fan_id)
        joblib.dump(iso_model, iso_path)
        self._models_cache[f"iso_{fan_id}"] = iso_model
        return True

    def train_fault_classifier(self, fan_id: str, n_samples_per_class: int = 300) -> bool:
        """Génère un dataset d'incidents étiquetés et entraîne le classifieur."""
        rng = np.random.default_rng(42)

        vib_0 = 2.5 + rng.normal(0, 0.1, n_samples_per_class)
        temp_0 = 45.0 + rng.normal(0, 0.5, n_samples_per_class)
        curr_0 = 12.0 + rng.normal(0, 0.2, n_samples_per_class)

        vib_1 = rng.uniform(3.5, 5.5, n_samples_per_class)
        temp_1 = 45.0 + rng.normal(0, 0.5, n_samples_per_class)
        curr_1 = 12.0 + rng.normal(0, 0.2, n_samples_per_class)

        vib_2 = 2.5 + rng.normal(0, 0.1, n_samples_per_class)
        temp_2 = 55.0 + rng.uniform(0, 15.0, n_samples_per_class)
        curr_2 = 14.0 + rng.uniform(0, 3.0, n_samples_per_class)

        X_train = pd.DataFrame({
            'vibration': np.concatenate([vib_0, vib_1, vib_2]),
            'temperature': np.concatenate([temp_0, temp_1, temp_2]),
            'current': np.concatenate([curr_0, curr_1, curr_2])
        })

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

    def ensure_models_trained(self, fan_id: str):
        """Vérifie la présence des modèles pour un capteur et les entraîne une seule fois si manquants."""
        iso_path, clf_path = self._get_model_paths(fan_id)

        if self._load_model(iso_path, f"iso_{fan_id}") is None:
            logger.info(f"Nouveau capteur ({fan_id}) : Initialisation unique d'Isolation Forest...")
            self.train_isolation_forest(fan_id)

        if self._load_model(clf_path, f"clf_{fan_id}") is None:
            logger.info(f"Nouveau capteur ({fan_id}) : Initialisation unique du Random Forest Classifier...")
            self.train_fault_classifier(fan_id)

    def predict(self, fan_id: str, df: pd.DataFrame) -> dict:
        if df is None or df.empty:
            return {
                "fan_id": fan_id, "status": "no_data", "health_status": "UNKNOWN",
                "faulty_feature": None, "fault_label": None, "points_count": 0, "data": []
            }

        # 1. Vérification & Entraînement automatique au besoin (1 seule fois par capteur)
        self.ensure_models_trained(fan_id)

        required_cols = ['vibration', 'temperature', 'current']
        if not all(col in df.columns for col in required_cols):
            return {
                "fan_id": fan_id, "status": "error", "health_status": "UNKNOWN",
                "ai_message": f"Colonnes requises manquantes. Nécessaires: {required_cols}"
            }

        time_col = '_time' if '_time' in df.columns else ('time' if 'time' in df.columns else None)

        records = [
            {
                "timestamp": str(row[time_col]) if time_col else None,
                **{col: (float(row[col]) if pd.notnull(row[col]) else None) for col in required_cols}
            }
            for _, row in df.iterrows()
        ]

        features = df[required_cols].dropna()
        if features.empty:
            return {
                "fan_id": fan_id, "status": "no_data", "health_status": "UNKNOWN",
                "faulty_feature": None, "fault_label": None, "points_count": 0, "data": records
            }

        last_row = df.iloc[-1]

        response = {
            "fan_id": fan_id,
            "status": "ok",
            "last_vibration": float(last_row['vibration']) if pd.notnull(last_row['vibration']) else None,
            "last_temperature": float(last_row['temperature']) if pd.notnull(last_row['temperature']) else None,
            "last_current": float(last_row['current']) if pd.notnull(last_row['current']) else None,
            "timestamp": str(last_row[time_col]) if time_col else None,
            "points_count": len(features),
            "data": records
        }

        # 2. Chargement des modèles entraînés
        iso_path, clf_path = self._get_model_paths(fan_id)
        iso_model = self._load_model(iso_path, f"iso_{fan_id}")
        clf_model = self._load_model(clf_path, f"clf_{fan_id}")

        if iso_model is None or clf_model is None:
            response.update({
                "health_status": "UNTRAINED",
                "faulty_feature": None,
                "fault_label": None,
                "ai_message": "Erreur lors de l'accès aux modèles."
            })
            return response

        # 3. Inférence ML & Calcul robuste du Z-Score
        last_point = features.iloc[[-1]]
        last_series = features.iloc[-1]

        if iso_model.predict(last_point)[0] == -1:
            health_status = "CRITICAL"

            if len(features) > 1:
                historical = features.iloc[:-1]
                means = historical.mean()
                stds = historical.std().fillna(1.0).replace(0, 1e-6)
            else:
                means = pd.Series({'vibration': 2.5, 'temperature': 45.0, 'current': 12.0})
                stds = pd.Series({'vibration': 0.1, 'temperature': 0.5, 'current': 0.2})

            z_scores = ((last_series - means) / stds).abs()
            faulty_feature = str(z_scores.idxmax())

            fault_code = int(clf_model.predict(last_point)[0])
            labels = {
                1: "Usure mécanique / Désalignement",
                2: "Surchauffe Moteur / Surcharge électrique"
            }
            fault_label = labels.get(fault_code, "Anomalie non classifiée")

            fault_val = float(last_series[faulty_feature])
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

    def update_last_predictions(self) -> None:
        """Récupère tous les fan_ids, exécute l'analyse pour chacun et sauve le résultat dans InfluxDB."""
        fan_ids = self.influx_repo.get_all_fan_ids()

        logger.info(f"Mise à jour des prédictions pour : {fan_ids}")

        for fan_id in fan_ids:
            try:
                df = self.influx_repo.get_recent_data(fan_id, minutes=1440)
                prediction = self.predict(fan_id, df)
                self.influx_repo.save_prediction(prediction)
            except Exception as e:
                logger.error(f"Échec de la mise à jour pour le ventilateur {fan_id}: {e}")

    def read_last_prediction(self, fan_id: str) -> dict:
        """
        Récupère la toute dernière prédiction pour un capteur spécifique.
        """
        if not fan_id:
            return {}

        df = self.influx_repo.get_latest_prediction_by_fan_id(fan_id)
        if df is None or df.empty:
            return {}

        # Nettoyage des colonnes métadonnées InfluxDB
        cols_to_drop = [c for c in ['result', 'table', '_start', '_stop', '_measurement'] if c in df.columns]
        df = df.drop(columns=cols_to_drop)

        if '_time' in df.columns:
            df = df.rename(columns={'_time': 'timestamp'})
            df['timestamp'] = df['timestamp'].astype(str)

        records = df.to_dict(orient='records')
        
        # Retourne uniquement le dernier objet prédit
        return records[0] if records else {}