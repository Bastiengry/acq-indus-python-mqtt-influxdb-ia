import asyncio
from app.repositories.influx_repo import InfluxRepository
from app.repositories.neo4j_repo import Neo4jRepository
from app.core.config import logger

class SyncService:
    def __init__(self):
        self.influx_repo = InfluxRepository()
        self.neo4j_repo = Neo4jRepository()

    def run_sync_logic(self):
        logger.info("--> [SYNC] Interrogation d'InfluxDB pour mise à jour du graphe...")
        try:
            tables = self.influx_repo.get_topology_data()
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
                logger.warning("--> [SYNC] Aucune donnée avec le tag 'fan_id' n'a été trouvée.")
                return

            self.neo4j_repo.update_topology(topology)
            logger.info(f"--> [SYNC SUCCESS] Topologie Neo4j mise à jour : {list(topology.keys())}")
        except Exception as e:
            logger.error(f"--> [SYNC ERROR] Échec synchronisation : {e}")

    async def sync_influx_to_neo4j(self):
        await asyncio.to_thread(self.run_sync_logic)