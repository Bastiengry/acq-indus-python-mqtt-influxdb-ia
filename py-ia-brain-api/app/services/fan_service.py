import logging
from app.repositories.influx_repo import InfluxRepository
import pandas as pd

logger = logging.getLogger(__name__)


class FanService:
    def __init__(self):
        self.influx_repo = InfluxRepository()

    def read_all_fan_ids(self) -> list[str]:
        """
        Délègue la récupération de la liste complète des fan_id à l'InfluxRepository.
        """
        try:
            return self.influx_repo.get_all_fan_ids()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des fan_ids : {e}")
            return []

    def read_data(self, fan_id: str, minutes: int = 5) -> list[dict]:
        """
        Lit et retourne la liste des dernières télémétries enregistrées pour un ventilateur.
        """
        try:
            df = self.influx_repo.get_recent_data(fan_id=fan_id, minutes=minutes)

            if df is None or df.empty:
                return []

            required_cols = ['vibration', 'temperature', 'current']
            time_col = '_time' if '_time' in df.columns else ('time' if 'time' in df.columns else None)

            # Formate chaque ligne du tableau en dictionnaire
            records = [
                {
                    "timestamp": str(row[time_col]) if time_col else None,
                    **{
                        col: (float(row[col]) if pd.notnull(row[col]) else None)
                        for col in required_cols
                        if col in df.columns
                    }
                }
                for _, row in df.iterrows()
            ]

            return records

        except Exception as e:
            logger.error(f"Erreur lors de la lecture des données pour {fan_id} : {e}")
            return []