# Flux
```
Simulateur Python -> Broker MQTT (Mosquitto) -> | -> Telegraf (Collecteur) -> InfluxDB (Séries Temporelles) -> IA Python -> Affichage Frontend (onglet "monitor")
                                                |                                                           -> Grafana + Affichage frontend (onglet "grafana")
                                                |
                                                |
                                                |
                                                | -> Gestionnaire d'alarmes
                                                |       (ThingsBoard)
                                                |            |
                                                |            | Ecriture dans un topic dédié aux alarmes
                                                |            | (Qui peut ensuite utiliser telegraf pour écrire en BDD)
                                                |            |
                                                | <-        <-
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
1. Se connecter à grafana à l'adresse "http://localhost:3001/"
2. Connexion : Login "admin" / Password "admin".
3. Ajouter une source de données :
	- Va dans Connections > Data Sources.
	- Choisis InfluxDB.
	- Paramétrage InfluxDB (Mode Flux) :
	- Query Language : Sélectionne Flux (très important pour InfluxDB 2.x).
	- URL : http://acq-indus-influxdb:8086 (on utilise le nom du container).
	- Auth : Désactive "Basic Auth" et utilise ton Token InfluxDB, ton Org (bg_soft) et ton Default Bucket (fan_telemetry).
	- Save & Test : Si le message est vert, Grafana "voit" tes données de vibration.
4. Créer ton premier Dashboard
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

# Frontend
1. Pour visualiser le frontend, se connecter à l'adresse "http://localhost:8080"

# ThingsBoard

## Configuration de ThingsBoard
1. Se connecter à ThingsBoard à l'adresse "http://localhost:9090/"
2. Connexion : Login "tenant@thingsboard.org" / Password "tenant"          (OU ==> "sysadmin@thingsboard.org" / "sysadmin").
3. Allez dans Entities >> Passerelle     (en français => Entités >> Appareils).
4. Cliquer sur le gros bouton "+" en haut à droite, puis sélectionnez Add new device (Ajouter un nouvel appareil).
	- Le nommer (ex: "Passerelle_ThingsBoard") puis cliquer sur Add.
	- Device Profile : Laissez default.
	- Cliquer sur Add (Ajouter).
5. Cliquer sur le bouton "Connectors configuration" :
	- Cliquer sur "Add connector" :
		* Type : MQTT
		* Name : MQTT
		* Cliquer sur "Ajouter"
6. Sur la droite, aller dans le menu "Connection to broker" :
	- Host : acq-indus-mosquitto
	- Port : 1883
	- Client ID : ThingsBoard_gateway
	- User : anonymous
7. Sur la droite, aller dans le menu "Data mapping" :
	- Supprimer toutes les lignes existantes
	- Cliquer sur "Add mapping" :
		* Topic filter : tunnel/fan/+/telemetry
		* Payload type: JSON
		* Appareil >> Name : ${fan_id}
		* Appareil >> Profile name : Ventilateur
		* Appareil >> Attributes : 
			- Cliquer sur "Modifier (symbole crayon)"
			- Cliquer sur "Add attribute" :
				* Key : vibration
				* Type : double
				* Value : ${vibration}
	- Valider tout
8. Une fois créée, cliquer sur la ligne correspond à la Gateway :
	- Sur la droite, aller dans le menu "General configuration" :
		* Dans l'onglet "General", générer un jeton d'accès (access token) pour que la Gateway puisse se connecter à ThingsBoard
		* Copier le Access Token
	- Coller l'access token dans le ".env"
	- Redémarrer le "docker compose" en forçant la recréation de ThingsBoard Gateway   ==>   "sudo docker compose up -d --force-recreate acq-indus-thingsboard-gateway"

## Visualisation dans ThingsBoard
1. Une fois les conteneurs redémarrés, la passerelle va commencer à écouter le broker Mosquitto.
2. Retourner sur l'interface web de ThingsBoard (http://localhost:9090).
3. Aller dans Entities >> Devices (Entités >> Dispositifs).
4. Magie : Un nouvel équipement nommé TUNNEL_NORD_01 (la valeur de la variable fan_id) s'est créé tout seul.
5. Cliquer dessus :
	- Aller dans l'onglet Latest Telemetry
	- Normalement, les données (produites par le simulateur Python en entrée du système) sont visibles 
