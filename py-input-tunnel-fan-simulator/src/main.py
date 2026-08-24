import os
import time
import json
import numpy as np
import paho.mqtt.client as mqtt
from datetime import datetime

MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt-broker")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

# Configuration avec types de pannes différenciés
FANS_CONFIG = [
    {"fan_id": "FAN_01", "location": "NORTH TUNNEL", "fail": True,  "fault_type": "vibration"},
    {"fan_id": "FAN_02", "location": "NORTH TUNNEL", "fail": False, "fault_type": "none"},
    {"fan_id": "FAN_03", "location": "SOUTH TUNNEL", "fail": True,  "fault_type": "overheat"},
    {"fan_id": "FAN_04", "location": "EAST TUNNEL",  "fail": True,  "fault_type": "current"},
]

class TunnelFanSimulator:
    def __init__(self, fan_id, location, simulate_failure=False, fault_type="none"):
        self.fan_id = fan_id
        self.location = location
        self.simulate_failure = simulate_failure
        self.fault_type = fault_type
        self.step = 0

    def get_telemetry(self):
        self.step += 1
        
        # Réinitialisation stricte du cycle de 10 secondes pour TOUS les ventilateurs
        if self.step > 20:
            self.step = 1

        # 1. Régime nominal (données saines)
        vibration = 2.5 + np.random.normal(0, 0.08)
        temp = 45.0 + np.random.normal(0, 0.3)
        current = 12.0 + np.random.normal(0, 0.1)

        # 2. Injection d'anomalie ciblée
        if self.simulate_failure and self.step >= 10:
            if self.fault_type == "vibration":
                # Usure mécanique / Désalignement
                vibration = 7.5 + np.random.normal(0, 0.2)
            elif self.fault_type == "overheat":
                # Surchauffe Moteur
                temp = 72.0 + np.random.normal(0, 0.8)
                current = 16.5 + np.random.normal(0, 0.3)
            elif self.fault_type == "current":
                # Surcharge électrique
                current = 24.0 + np.random.normal(0, 0.5)

        return {
            "timestamp": datetime.now().isoformat(),
            "fan_id": self.fan_id,
            "vibration": round(vibration, 3),
            "temperature": round(temp, 2),
            "current": round(current, 2),
            "location": self.location,
            "status": "warning" if vibration > 3.0 or temp > 60.0 or current > 18.0 else "nominal"
        }

def main():
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        simulators = [
            TunnelFanSimulator(
                fan_id=cfg["fan_id"], 
                location=cfg["location"], 
                simulate_failure=cfg["fail"],
                fault_type=cfg.get("fault_type", "none")
            ) 
            for cfg in FANS_CONFIG
        ]
        
        print(f"Démarrage de la simulation pour {len(simulators)} ventilateurs...")
        
        while True:
            for fan in simulators:
                data = fan.get_telemetry()
                topic = f"tunnel/fan/{fan.fan_id}/telemetry"
                client.publish(topic, json.dumps(data))
                print(f"[{data['fan_id']}] ({data['location']}) - Vib: {data['vibration']} | Temp: {data['temperature']}°C | Curr: {data['current']}A | Status: {data['status']}")
            
            time.sleep(1)
            
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()