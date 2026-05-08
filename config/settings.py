"""
Zentrale Konfiguration fuer das Buchanalyse-Projekt.
Alle Pfade und Einstellungen an einem Ort.
"""

import os

# --- Pfade ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIBLIOTHEK_DIR = r"E:\Bucher"
ANALYSEN_DIR = os.path.join(BASE_DIR, "analysen")
BIBLIOTHEK_JSON = os.path.join(BASE_DIR, "bibliothek", "index.json")
QUERVERBINDUNGEN_JSON = os.path.join(BASE_DIR, "bibliothek", "querverbindungen.json")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# --- Analyse-Modi ---
STANDARD_OUTPUTS = ("lektor", "analyse")
FULL_OUTPUTS = ("lektor", "analyse", "vernetzung", "bericht")
AUTO_DELTA_VERNETZUNG = False
AUTO_WIKI_KURATOR = False

# --- Modellstrategie ---
ANALYSE_MODEL = "claude-sonnet-4-6"
VERNETZUNG_RELEVANZ_MODEL = "claude-haiku-4-5-20251001"
LEKTOR_PROVIDER = "ollama"
LEKTOR_MODEL = "qwen2.5:14b-instruct"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "32768"))

# --- Agent-Einstellungen ---
MAX_TURNS = 20
