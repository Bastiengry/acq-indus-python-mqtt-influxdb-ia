import os
import time
import json
import numpy as np
import paho.mqtt.client as mqtt
from datetime import datetime

# Configuration via variables d'environnement (plus flexible)
MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt-broker")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

# Définition des ventilateurs et de leurs localisations
FANS_CONFIG = [
    {"fan_id": "FAN_01", "location": "NORTH TUNNEL", "fail": True},
    {"fan_id": "FAN_02", "location": "NORTH TUNNEL", "fail": False},
    {"fan_id": "FAN_03", "location": "SOUTH TUNNEL", "fail": True},
    {"fan_id": "FAN_04", "location": "EAST TUNNEL", "fail": False},
]

class TunnelFanSimulator:
    def __init__(self, fan_id, location, simulate_failure=False):
        self.fan_id = fan_id
        self.location = location
        self.simulate_failure = simulate_failure
        self.step = 0
        
    def get_telemetry(self):
        self.step += 1
        
        if self.simulate_failure and self.step > 80:
            self.step = 1
        
        # 1. Base normale (Bruit gaussien)
        vibration = 2.5 + np.random.normal(0, 0.1)
        temp = 45.0 + np.random.normal(0, 0.5)
        current = 12.0 + np.random.normal(0, 0.2)
        
        # 2. Simulation de la dégradation
        if self.simulate_failure and self.step > 50:
            severity = (self.step - 50) * 0.05
            vibration += severity * 0.8
            temp += severity * 0.3
            current += severity * 0.1
            
        return {
            "timestamp": datetime.now().isoformat(),
            "fan_id": self.fan_id,
            "vibration": round(vibration, 3),
            "temperature": round(temp, 2),
            "current": round(current, 2),
            "location": self.location,
            "status": "warning" if vibration > 3.0 else "nominal"
        }

def main():
    # Initialisation MQTT
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        simulators = [
            TunnelFanSimulator(
                fan_id=cfg["fan_id"], 
                location=cfg["location"], 
                simulate_failure=cfg["fail"]
            ) 
            for cfg in FANS_CONFIG
        ]
        
        print(f"Démarrage de la simulation pour {len(simulators)} ventilateurs...")
        
        while True:
            for fan in simulators:
                data = fan.get_telemetry()
                
                topic = f"tunnel/fan/{fan.fan_id}/telemetry"
                client.publish(topic, json.dumps(data))
                print(f"[{data['fan_id']}] ({data['location']}) - Vib: {data['vibration']} mm/s | Temp: {data['temperature']}°C")
            
            time.sleep(1)
            
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()