import os
import logging
from influxdb_client import InfluxDBClient
from neo4j import GraphDatabase
import ollama

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_hypervisor_api")

INFLUX_URL = os.getenv("INFLUXDB_URL", "http://acq-indus-influxdb:8086")
INFLUX_TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUX_ORG = os.getenv("INFLUXDB_ORG", "bg_soft")
INFLUX_BUCKET = os.getenv("INFLUXDB_BUCKET", "fan_telemetry")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://acq-indus-neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://acq-indus-ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

# Initialisation des clients
influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
client_ollama = ollama.Client(host=OLLAMA_HOST)