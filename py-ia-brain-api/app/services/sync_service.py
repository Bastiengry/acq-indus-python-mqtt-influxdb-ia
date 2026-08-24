import pandas as pd
from app.repositories.influx_repo import InfluxRepository
from app.repositories.neo4j_repo import Neo4jRepository
from app.core.config import logger

class SyncService:
    def __init__(self):
        self.influx_repo = InfluxRepository()
        self.neo4j_repo = Neo4jRepository()

    def sync_influx_to_neo4j(self):  # <-- SUPPRIMER "async" ICI
        logger.info("--> [SYNC] Interrogation d'InfluxDB pour mise à jour du graphe...")
        try:
            df = self.influx_repo.get_topology_data()
            
            if df is None or df.empty:
                logger.warning("--> [SYNC] Aucune donnée de topologie renvoyée par InfluxDB.")
                return

            topology = {}

            for _, row in df.iterrows():
                fan_id = row.get("fan_id")
                location = row.get("location") if pd.notnull(row.get("location")) else "Unknown"
                field = row.get("_field")
                
                if pd.notnull(fan_id) and pd.notnull(field) and fan_id and field:
                    if fan_id not in topology:
                        topology[fan_id] = {"sensors": set(), "location": location}
                    topology[fan_id]["sensors"].add(field)

            if not topology:
                logger.warning("--> [SYNC] Aucune donnée avec le tag 'fan_id' n'a été trouvée.")
                return

            self.neo4j_repo.update_topology(topology)
            logger.info(f"--> [SYNC SUCCESS] Topologie Neo4j mise à jour : {list(topology.keys())}")

        except Exception as e:
            logger.error(f"--> [SYNC ERROR] Échec synchronisation : {e}")