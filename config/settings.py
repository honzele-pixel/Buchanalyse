"""
Zentrale Konfiguration für das Buchanalyse-Projekt.
Alle Pfade und Einstellungen an einem Ort.
"""

import os

# --- Pfade ---
BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIBLIOTHEK_DIR = r"E:\Bucher"          # Wo die PDFs liegen
ANALYSEN_DIR   = os.path.join(BASE_DIR, "analysen")
BIBLIOTHEK_JSON = os.path.join(BASE_DIR, "bibliothek", "index.json")
QUERVERBINDUNGEN_JSON = os.path.join(BASE_DIR, "bibliothek", "querverbindungen.json")
LOGS_DIR       = os.path.join(BASE_DIR, "logs")

# --- Modell ---
MODEL = "claude-opus-4-6"

# --- Agent-Einstellungen ---
MAX_TURNS = 20
