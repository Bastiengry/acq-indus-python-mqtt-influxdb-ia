# Flux de données de l'application
```
Simulateur Python -> Broker MQTT (Mosquitto) -> | -> Telegraf (Collecteur) -> InfluxDB (Séries Temporelles) -> IA Python -> application Frontend supervision (onglet "monitor")
                                                |                                                           -> application Grafana     + application Frontend supervision (onglet "grafana")
                                                |
                                                |
                                                |
                                                | -> Gestionnaire d'alarmes
                                                |       (Grafana alerting)
                                                |            |
                                                |            | Ecriture dans un topic dédié aux alarmes
                                                |            | (Puis telegraf écrit en BDD)
                                                |            |
                                                | <-        <-
```


# A REINSTALLER MANUELLEMENT LA PREMIERE FOIS (NON PRIS EN CHARGE PAR DOCKER COMPOSE)
1. Générer le TOKEN InfluxDB
2. Charger le modèle de LLM pour le chatbot


# Génération du token dans influxdb
1. Se connecter à influxdb à l'adresse "http://localhost:8086/"
2. Saisir le login et le mot de passe (cf. docker-compose.yml)
3. Aller dans "Load Data" (elle ressemble à un petit bac avec une flèche) >> "API Tokens"
4. Cliquer sur le bouton "GENERATE API TOKEN" >> "Custom API Token"
5. Saisir le nom du token : "fan_telemetry_token"
6. Choisir les accès READ/WRITE pour le bucket "fan_telemetry"
7. Cliquer sur "GENERATE"
8. Copier le token et le coller dans le champ "INFLUX_TOKEN" du fichier ".env"


# Lancer docker compose
- Simple : docker compose up
- Avec compilation : docker compose up --build


# Arrêter docker compose
- Simple : docker compose down
- Avec suppression des volumes : docker compose down -v


# S'abonner au topic MQTT dans mosquitto pour débugger
sudo docker exec -it acq-indus-mosquitto mosquitto_sub -h localhost -t "#" -v


# Objets 3D (.glb)
- Quaternius
- Sketchfab
- Poly Haven


# Grafana : connecter la base influxdb  
**==> AUTOCONFIGURE DANS LE docker-compose.yml (et via un fichier de configuration)**
1. Se connecter à grafana à l'adresse "http://localhost:3001/"
2. Connexion : Login "admin" / Password "admin".
3. Ajouter une source de données :
	- Aller dans "Connections > Data Sources".
	- Cliquer sur "Add new data source".
	- Choisir "InfluxDB".
	- Paramétrage InfluxDB (Mode Flux) :
		* Query Language : Sélectionner Flux (très important pour InfluxDB 2.x).
		* URL : http://acq-indus-influxdb:8086 (on utilise le nom du container).
		* Auth : 
			- Désactiver "Basic Auth"
			- Renseigner le champ du token avec le Token InfluxDB
			- Renseigner le champ de l'organisation avec "bg_soft"
			- Renseigner le champ "Default Bucket" avec "fan_telemetry".
		* Cliquer sur "Save & Test" : Si le message est vert, la configuration est correcte.


# Grafana : afficher un dashboard avec les données du capteur d'entrée
**==> AUTOCONFIGURE DANS LE docker-compose.yml (et via un fichier de configuration)**
1. Se connecter à Grafana à l'adresse "http://localhost:3001/"
2. Connexion : Login "admin" / Password "admin".
3. Créer un Dashboard :
	- Aller dans "Connections > Dashboards".
	- Cliquer sur "Create Dashboard".
	- Cliquer sur "Add Visualization".
	- Sélectionner la data source "InfluxDB".
	- Dans l'éditeur de requête, utiliser ce code Flux :
		- Extrait de code :
			```from(bucket: "fan_telemetry")
			   |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
			   |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer")
			   |> filter(fn: (r) => r["fan_id"] == "TUNNEL_NORD_01")
			   |> filter(fn: (r) => r["_field"] == "vibration")
			   |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
			   |> yield(name: "mean")```
	- Cliquer sur "Save".
	- Dans l'encart qui s'affiche :
		* Donner un nom au dashboard.
		* Cliquer sur "Save".


# Grafana : afficher les logs
**==> AUTOCONFIGURE DANS LE docker-compose.yml (et via un fichier de configuration)**
**==> PASSER DIRECTEMENT AU POINT 4 POUR VISUALISER LES LOGS
1. Se connecter à Grafana à l'adresse "http://localhost:3001/"
2. Connexion : Login "admin" / Password "admin".
3. Ajouter une source de données :
	- Aller dans "Connections > Data Sources".
	- Cliquer sur "Add new data source".
	- Choisir "Loki".
	- Paramétrage Loki :
		* URL : http://acq-indus-loki:3100 (on utilise le nom du container).
		* Cliquer sur "Save & Test" : Si le message est vert, la configuration est correcte.
4. Aller dans l'onglet "Explore"
	- Choisir la source "Loki" :
		* Section "Label filters" :
			- Select Label : container
			- Operator : "="
			- Select Value : acq-indus-influxdb
	- Cliquer sur le bouton "Run query" dans la barre du haut de l'application.

# Grafana : configuration des alarmes
**==> AUTOCONFIGURE DANS LE docker-compose.yml (et via un fichier de configuration)**
1. Se connecter à Grafana à l'adresse "http://localhost:3001/"
2. Connexion : Login "admin" / Password "admin".
3. Ajouter un point de contact :
	- Aller dans le menu "Alerting >> Contact points".
	- Cliquer sur le gros bouton "+ Add contact point".
	- Donner un nom (ex: "acq-indus-alarm").
	- Choisir l'intégration "Webhook".
	- Dans l'URL, saisir l'adresse interne du conteneur Telegraf : http://acq-indus-telegraf:8087/grafana-webhook.
	- Cliquer sur "Test" (Telegraf recevra un payload de test), puis "Save contact point".
4. Associer le point de contact à la politique de notification globale
	- Dans Grafana, les règles d'alertes n'envoient pas directement les données à un point de contact. Elles passent par une Notification Policy (Politique de notification) qui joue le rôle de répartiteur.
	- Dans le menu de gauche, aller dans "Alerting > Notification policies".
	- Sur la ligne nommée "Default policy" :
		* Cliquer sur les trois petits points à droite.
		* Cliquer sur "Edit".
		* Dans le champ "Default contact point", sélectionner "acq-indus-alarm".
		* Cliquez sur le bouton "Update default policy".
5. Créer la règle d'alerte
	- Dans le menu de gauche, aller dans "Alerting > Alert rules".
	- Cliquer sur le bouton "New alert rule" :
		* Donner un nom "acq-indus-alarm-rule"
		* Choisir "InfluxDb"
		* Dans la section "2. Define query and alert condition" :
			- Définir la requête :
				```from(bucket: "fan_telemetry")
				  |> range(start: -1m)
				  |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer")
				  |> filter(fn: (r) => r["_field"] == "vibration")
				```
			- Définir la condition de déclenchement dans "Expression" :
				* Bloc B (Reduce) :
					- Input : A (cet input correspond à la requête définie plus haut)
					- Function : Last
				* Bloc C (Threshold / Seuil) :
					- Input : B
						* Configurez le seuil : IS ABOVE 2.5 (Puisque le simulateur monte parfois à 3.66 en mode warning, cela va forcer l'alerte à se déclencher immédiatement).
		* Dans la section "3. Set evaluation behavior" :
			- Cliquer sur "New folder"
				* Donner le nom "acq-indus-alarm-eval-folder"
			- Cliquer sur "New evaluation group" :
				* Donner le nom "acq-indus-alarm-eval-grp"
				* Définir la "Pending Period" à "1m" (==> 1 minute)
	- Cliquer sur le bouton "Save rule and exit" en haut à droite


# Portail web frontend
1. Pour visualiser le portail frontend, se connecter à l'adresse "http://localhost:8080"


# Supervision frontend
1. Pour visualiser le frontend de supervision, se connecter à l'adresse "http://localhost:8081" ou cliquer sur le lien dans l'application de portail web

2. Pour utiliser le chatbot, il faut installer le modèle du LLM : "docker exec -it acq-indus-ollama ollama run qwen2.5:3b"

# Neo4j (knowledge graph)
1. Se connecter à l'IHM à l'adresse "http://localhost:7474"
2. Utilisateur / mot de passe : neo4j / password123
3. Dans la barre de recherche en haut, pour voir les topologies, taper la requête CIPHER : "MATCH (n) RETURN n"
3. Dans la barre de recherche en haut, pour supprimer les topologies, taper la requête CIPHER : "MATCH (n) DETACH DELETE n"
