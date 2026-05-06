"""Direktstart Quellenextraktor für Eiszeit (Krone-Schmalz)."""
import sys
import os
sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

from agents.quellenextraktor import quellenextraktor_starten

buch = {
    "autor":    "Gabriele Krone-Schmalz",
    "titel":    "Eiszeit",
    "pdf_pfad": r"E:\Bucher\Gabriele_Krone_Schmalz\Eiszeit.pdf",
}

ausgabe_pfad = r"E:\Claude_Projekte\Buchanalysen\analysen\Gabriele_Krone_Schmalz\Eiszeit\05_quellen.md"

quellenextraktor_starten(buch, ausgabe_pfad)
