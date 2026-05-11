# Flux
```
Simulateur Python -> Protocole MQTT (Mosquitto) -> Telegraf (Collecteur) -> InfluxDB (Séries Temporelles) -> IA Python -> Affichage Frontend (onglet "monitor")
                                                                                                          -> Grafana + Affichage frontend (onglet "grafana")
```

# Génération du token dans influxdb
1. Se connecter à influxdb à l'adresse "http://localhost:8086/"
2. Saisir le login et le mot de passe (cf. docker-compose.yml)
3. Aller dans "Load Data" (elle ressemble à un petit bac avec une flèche) >> "API Tokens"
4. Cliquer sur le bouton "GENERATE API TOKEN" >> "Custom API Token"
5. Saisir le nom du token : "fan_telemetry_token"
6. Choisir les accès READ/WRITE pour le bucket "fan_telemetry"
7. Cliquer sur "GENERATE"
8. Copier le token et le coller dans le champ "token" du fichier de configuration "telegraf.conf" du service telegraf


# Lancer docker compose
- Simple : docker compose up
- Avec compilation : docker compose up --build


# Arrêter docker compose
- Simple : docker compose down
- Avec suppression des volumes : docker compose down -v

# Objets 3D (.glb)
- Quaternius
- Sketchfab
- Poly Haven

# Grafana
1. Connexion : Login admin / Password admin.
2. Ajouter une source de données :
	- Va dans Connections > Data Sources.
	- Choisis InfluxDB.
	- Paramétrage InfluxDB (Mode Flux) :
	- Query Language : Sélectionne Flux (très important pour InfluxDB 2.x).
	- URL : http://acq-indus-influxdb:8086 (on utilise le nom du container).
	- Auth : Désactive "Basic Auth" et utilise ton Token InfluxDB, ton Org (bg_soft) et ton Default Bucket (fan_telemetry).
	- Save & Test : Si le message est vert, Grafana "voit" tes données de vibration.
3. Créer ton premier Dashboard
	- Maintenant que Grafana est relié, tu peux créer un graphique professionnel :
	- Crée un nouveau Dashboard et ajoute une "Visualization".
	- Dans l'éditeur de requête, utilise ce code Flux (similaire à celui de ton IA) :
	- Extrait de code
		```from(bucket: "fan_telemetry")
		  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
		  |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer")
		  |> filter(fn: (r) => r["fan_id"] == "TUNNEL_NORD_01")
		  |> filter(fn: (r) => r["_field"] == "vibration")
		  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
		  |> yield(name: "mean")```