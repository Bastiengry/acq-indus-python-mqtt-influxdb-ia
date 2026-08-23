import json
import asyncio
from app.core.config import client_ollama, OLLAMA_MODEL, logger
from app.repositories.neo4j_repo import Neo4jRepository
from app.services.anomaly_service import AnomalyService

OLLAMA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_network_topology",
            "description": "Obtenir la structure globale du réseau (tunnels et équipements)."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_sensor_list",
            "description": "Obtenir la liste détaillée de TOUS les capteurs."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_eqp_or_sensor_health",
            "description": "Obtenir l'état de santé et les valeurs d'un équipement ou d'un capteur.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_id": {"type": "string", "description": "L'identifiant exact (ex: FAN_01 ou FAN_01_TEMPERATURE)."}
                },
                "required": ["target_id"]
            }
        }
    }
]

class LLMService:
    def __init__(self):
        self.neo4j_repo = Neo4jRepository()
        self.anomaly_service = AnomalyService()

    def resolve_fan_and_sensor(self, target_id: str):
        target_clean = target_id.strip()
        res = self.neo4j_repo.resolve_sensor(target_clean)
        if res:
            return res["fan_id"], res["sensor_type"].lower()
            
        for metric in ["temperature", "vibration", "current"]:
            if target_clean.lower().endswith(f"_{metric}"):
                return target_clean[:-len(metric)-1], metric
        return target_clean, None

    async def tool_check_health(self, target_id: str) -> str:
        try:
            fan_id, sensor_type = self.resolve_fan_and_sensor(target_id)
            res = self.anomaly_service.analyze_fan(fan_id)

            if sensor_type:
                val = res.get(f"last_{sensor_type}")
                return json.dumps({
                    "sensor_id": target_id, "fan_id": fan_id, "sensor_type": sensor_type,
                    "value": val, "timestamp": res.get("timestamp"),
                    "health_status": res.get("health_status"),
                    "is_anomalous": (res.get("faulty_feature") == sensor_type)
                })
            return json.dumps(res)
        except Exception as e:
            return f"Erreur analyse santé pour '{target_id}': {str(e)}"

    async def process_chat(self, user_msg: str) -> str:
        messages = [
            {"role": "system", "content": "Tu es un assistant IA de supervision industrielle. Sois précis et réponds en français."},
            {"role": "user", "content": user_msg}
        ]

        response = await asyncio.to_thread(
            client_ollama.chat, model=OLLAMA_MODEL, messages=messages, tools=OLLAMA_TOOLS
        )
        message = response['message']

        while message.get('tool_calls'):
            messages.append(message)
            for tool in message['tool_calls']:
                func_name = tool['function']['name']
                raw_args = tool['function']['arguments']
                args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

                if func_name == "get_network_topology":
                    result = await asyncio.to_thread(self.neo4j_repo.get_network_topology)
                elif func_name == "get_sensor_list":
                    result = await asyncio.to_thread(self.neo4j_repo.get_sensor_list)
                elif func_name == "check_eqp_or_sensor_health":
                    target = args.get("target_id") or args.get("fan_id", "")
                    result = await self.tool_check_health(target)
                else:
                    result = "Outil inconnu"

                messages.append({"role": "tool", "content": str(result)})

            response = await asyncio.to_thread(
                client_ollama.chat, model=OLLAMA_MODEL, messages=messages, tools=OLLAMA_TOOLS
            )
            message = response['message']

        return message['content']