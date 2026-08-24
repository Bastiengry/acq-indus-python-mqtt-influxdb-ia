import json
import asyncio
from app.core.config import client_ollama, OLLAMA_MODEL, logger
from app.repositories.neo4j_repo import Neo4jRepository
from app.services.fan_machine_learning_service import FanMachineLearningService
from app.services.fan_service import FanService

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
            "description": "Obtenir l'état de santé et les dernières valeurs d'un équipement ou capteur.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_id": {
                        "type": "string",
                        "description": "L'identifiant exact (ex: FAN_01 ou FAN_01_TEMPERATURE)."
                    }
                },
                "required": ["target_id"]
            }
        }
    }
]


class LLMService:
    def __init__(self):
        self.neo4j_repo = Neo4jRepository()
        self.fan_service = FanService()
        self.fan_machine_learning_service = FanMachineLearningService()

    def resolve_fan_and_sensor(self, target_id: str):
        target_clean = target_id.strip()
        res = self.neo4j_repo.resolve_sensor(target_clean)
        if res:
            return res["fan_id"], res["sensor_type"].lower()

        for metric in ["temperature", "vibration", "current"]:
            if target_clean.lower().endswith(f"_{metric}"):
                return target_clean[:-len(metric) - 1], metric
        return target_clean, None

    async def tool_check_health(self, target_id: str) -> str:
        try:
            fan_id, sensor_type = self.resolve_fan_and_sensor(target_id)
            
            # 1. Récupération de la dernière télémesure
            data_res = await asyncio.to_thread(self.fan_service.read_data, fan_id)
            
            # 2. Récupération de la dernière prédiction stockée
            pred_res = await asyncio.to_thread(self.fan_machine_learning_service.read_last_prediction, fan_id)

            # --- SÉCURISATION : Extraction du 1er élément si le service renvoie une liste ---
            if isinstance(data_res, list):
                data_res = data_res[0] if len(data_res) > 0 else {}
            if not isinstance(data_res, dict):
                data_res = {}

            if isinstance(pred_res, list):
                pred_res = pred_res[0] if len(pred_res) > 0 else {}
            if not isinstance(pred_res, dict):
                pred_res = {}

            # Fusion sécurisée des deux dictionnaires
            combined = {**data_res, **pred_res}

            if not combined:
                return json.dumps({"error": f"Aucune donnée trouvée pour '{target_id}'"})

            if sensor_type:
                val = combined.get(f"last_{sensor_type}")
                return json.dumps({
                    "sensor_id": target_id,
                    "fan_id": fan_id,
                    "sensor_type": sensor_type,
                    "value": val,
                    "timestamp": combined.get("timestamp"),
                    "health_status": combined.get("health_status", "UNKNOWN"),
                    "is_anomalous": (combined.get("faulty_feature") == sensor_type)
                })
                
            return json.dumps(combined)
        except Exception as e:
            logger.error(f"Erreur tool_check_health pour {target_id}: {e}")
            return f"Erreur analyse santé pour '{target_id}': {str(e)}"

    async def process_chat(self, user_msg: str) -> str:
        messages = [
            {"role": "system", "content": "Tu es un assistant IA de supervision industrielle. Sois précis et réponds en français."},
            {"role": "user", "content": user_msg}
        ]

        response = await asyncio.to_thread(
            client_ollama.chat, model=OLLAMA_MODEL, messages=messages, tools=OLLAMA_TOOLS
        )
        
        # Le client officiel Ollama utilise l'accès par attribut
        msg_obj = response.message

        # Résolution des Tool Calls (limité à 5 itérations max pour éviter les boucles infinies)
        max_iterations = 5
        iteration = 0

        while msg_obj.tool_calls and iteration < max_iterations:
            iteration += 1
            messages.append(msg_obj)

            for tool in msg_obj.tool_calls:
                func_name = tool.function.name
                raw_args = tool.function.arguments
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
            msg_obj = response.message

        return msg_obj.content or "Aucune réponse générée."