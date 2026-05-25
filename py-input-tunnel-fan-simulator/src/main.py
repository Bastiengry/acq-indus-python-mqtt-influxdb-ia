import os
import time
import json
import numpy as np
import paho.mqtt.client as mqtt
from datetime import datetime

# Configuration via variables d'environnement (plus flexible)
MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt-broker")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
FAN_ID = os.getenv("FAN_ID", "FAN_01")
MQTT_TOPIC = "tunnel/fan/{FAN_ID}/telemetry"

class TunnelFanSimulator:
    def __init__(self, fan_id):
        self.fan_id = fan_id
        self.step = 0
        
    def get_telemetry(self, simulate_failure=False):
        self.step += 1
        
        if simulate_failure and self.step > 80:
            self.step = 1
        
        # 1. Base normale (Bruit gaussien)
        vibration = 2.5 + np.random.normal(0, 0.1)
        temp = 45.0 + np.random.normal(0, 0.5)
        current = 12.0 + np.random.normal(0, 0.2)
        
        # 2. Simulation de la dégradation
        if simulate_failure and self.step > 50:
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
            "status": "warning" if vibration > 3.0 else "nominal"
        }

def main():
    # Initialisation MQTT
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        fan = TunnelFanSimulator(FAN_ID)
        print(f"Démarrage de la simulation pour {FAN_ID}...")

        while True:
            data = fan.get_telemetry(simulate_failure=True)
            client.publish(MQTT_TOPIC, json.dumps(data))
            print(f"[{data['status']}] Vibration: {data['vibration']} mm/s")
            time.sleep(1)
            
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()