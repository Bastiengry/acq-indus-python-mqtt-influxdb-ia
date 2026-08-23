import json
from app.core.config import neo4j_driver

class Neo4jRepository:
    def update_topology(self, topology: dict):
        cypher_query = """
        MERGE (t:Tunnel {id: $location})
        ON CREATE SET t.name = $location
        
        MERGE (f:Fan {id: $fan_id})
        ON CREATE SET f.name = $fan_id
        MERGE (t)-[:HAS_EQUIPMENT]->(f)
        MERGE (f)-[:LOCATED_IN]->(t)

        WITH f
        UNWIND $sensors AS sensor_type
        MERGE (s:Sensor {id: $fan_id + "_" + toUpper(sensor_type)})
        ON CREATE SET s.type = sensor_type
        MERGE (f)-[:HAS_SENSOR]->(s)
        MERGE (s)-[:MONITORS]->(f)
        """
        with neo4j_driver.session() as session:
            for fan_id, data in topology.items():
                session.run(
                    cypher_query, 
                    fan_id=fan_id, 
                    sensors=list(data["sensors"]), 
                    location=data["location"]
                )

    def get_fan_context(self, fan_id: str):
        query = """
        MATCH (f:Fan {id: $fan_id})-[:LOCATED_IN]->(t:Tunnel)
        OPTIONAL MATCH (f)<-[:MONITORS]-(s:Sensor)
        RETURN t.name as tunnel, f.name as name, collect(s.id) as sensors
        """
        with neo4j_driver.session() as session:
            result = session.run(query, fan_id=fan_id).single()
            return dict(result) if result else None

    def get_network_topology(self) -> str:
        query = """
        MATCH (t:Tunnel)<-[:LOCATED_IN]-(f:Fan)
        OPTIONAL MATCH (f)-[:HAS_SENSOR]->(s:Sensor)
        RETURN t.name as tunnel, f.id as fan_id, collect(s.id) as sensors
        """
        with neo4j_driver.session() as session:
            return json.dumps(session.run(query).data())

    def get_sensor_list(self) -> str:
        query = """
        MATCH (s:Sensor)-[:MONITORS]->(f:Fan)
        RETURN s.id as sensor_id, s.type as type, f.id as fan_id
        ORDER BY f.id, s.type
        """
        with neo4j_driver.session() as session:
            return json.dumps(session.run(query).data())

    def resolve_sensor(self, target_clean: str):
        query = "MATCH (s:Sensor {id: $id})-[:MONITORS]->(f:Fan) RETURN f.id as fan_id, s.type as sensor_type"
        with neo4j_driver.session() as session:
            return session.run(query, id=target_clean).single()