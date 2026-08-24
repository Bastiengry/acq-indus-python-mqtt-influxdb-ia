import logging
from datetime import datetime, timezone
import pandas as pd
import warnings

from influxdb_client import Point
from app.core.config import influx_client, INFLUX_BUCKET, INFLUX_ORG
from influxdb_client.client.warnings import MissingPivotFunction  # <-- Ligne 1

# Masque le warning d'absence de pivot dans le client InfluxDB
warnings.simplefilter("ignore", MissingPivotFunction)

logger = logging.getLogger(__name__)


class InfluxRepository:
    def __init__(self):
        self.client = influx_client
        self.query_api = self.client.query_api()
        self.write_api = self.client.write_api()
        self.bucket = INFLUX_BUCKET
        self.org = INFLUX_ORG

    def get_topology_data(self) -> pd.DataFrame:
        """
        Récupère la topologie et retourne un DataFrame Pandas
        pour être facilement consommé par SyncService.
        """
        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: -30d)
          |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer" or r["_measurement"] == "fan_telemetry")
          |> keep(columns: ["fan_id", "location", "_field"])
          |> group(columns: ["fan_id", "location", "_field"])
          |> distinct(column: "_field")
        '''
        try:
            df = self.query_api.query_data_frame(query)
            if isinstance(df, list):
                df = pd.concat(df, ignore_index=True) if df else pd.DataFrame()
            return df
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la topologie : {e}")
            return pd.DataFrame()

    def get_all_fan_ids(self) -> list[str]:
        """
        Récupère directement la liste de tous les fan_id depuis le catalogue de tags.
        """
        query = f'''
        import "influxdata/influxdb/schema"

        schema.tagValues(
          bucket: "{self.bucket}",
          tag: "fan_id",
          start: 0
        )
        '''
        try:
            df = self.query_api.query_data_frame(query)

            if isinstance(df, list):
                df = pd.concat(df, ignore_index=True) if df else pd.DataFrame()

            if df.empty or '_value' not in df.columns:
                return []

            # En Flux, schema.tagValues renvoie les valeurs dans la colonne '_value'
            return df['_value'].dropna().unique().tolist()

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des fan_ids : {e}")
            return []

    def get_recent_data(self, fan_id: str, minutes: int = 5) -> pd.DataFrame:
        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: -{minutes}m)
          |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer" or r["_measurement"] == "fan_telemetry")
          |> filter(fn: (r) => r["fan_id"] == "{fan_id}")
          |> filter(fn: (r) => r["_field"] == "vibration" or r["_field"] == "temperature" or r["_field"] == "current")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> group()
          |> sort(columns: ["_time"])
          |> tail(n: 300)
        '''
        result = self.query_api.query_data_frame(query)

        if isinstance(result, list):
            if not result:
                return pd.DataFrame()
            return pd.concat(result, ignore_index=True)
        return result

    def save_prediction(self, prediction: dict) -> bool:
        """Enregistre le résultat du diagnostic IA dans InfluxDB."""
        if not prediction or prediction.get("status") != "ok":
            return False

        try:
            fan_id = prediction.get("fan_id")
            health_status = prediction.get("health_status", "UNKNOWN")

            point = (
                Point("fan_predictions")
                .tag("fan_id", fan_id)
                .field("health_status", health_status)
                .field("faulty_feature", prediction.get("faulty_feature") or "none")
                .field("fault_label", prediction.get("fault_label") or "none")
                .field("ml_message", prediction.get("ml_message") or "")
                .field("last_vibration", prediction.get("last_vibration", 0.0) or 0.0)
                .field("last_temperature", prediction.get("last_temperature", 0.0) or 0.0)
                .field("last_current", prediction.get("last_current", 0.0) or 0.0)
                .time(datetime.now(timezone.utc))
            )

            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True

        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la prédiction dans InfluxDB : {e}")
            return False

    def get_latest_prediction_by_fan_id(self, fan_id: str) -> pd.DataFrame:
        """Récupère la toute dernière prédiction enregistrée dans InfluxDB pour un fan_id spécifique."""
        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: -7d)
          |> filter(fn: (r) => r["_measurement"] == "fan_predictions")
          |> filter(fn: (r) => r["fan_id"] == "{fan_id}")
          |> last()
          |> pivot(rowKey: ["_time", "fan_id"], columnKey: ["_field"], valueColumn: "_value")
        '''
        try:
            df = self.query_api.query_data_frame(query)
            if isinstance(df, list):
                df = pd.concat(df, ignore_index=True) if df else pd.DataFrame()
            return df
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la prédiction pour {fan_id} : {e}")
            return pd.DataFrame()

    def close(self):
        """Ferme la connexion au client InfluxDB."""
        self.client.close()