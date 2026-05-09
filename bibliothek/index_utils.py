from __future__ import annotations

import json
import os
from datetime import date


BIBLIOTHEK_INDEX = r"E:\Claude_Projekte\Buchanalysen\bibliothek\index.json"


def bibliothek_laden() -> dict:
    """Laedt den aktuellen Stand des Bibliotheksindex."""
    with open(BIBLIOTHEK_INDEX, "r", encoding="utf-8") as handle:
        return json.load(handle)


def bibliothek_speichern(daten: dict) -> None:
    """Speichert den aktualisierten Bibliotheksindex."""
    with open(BIBLIOTHEK_INDEX, "w", encoding="utf-8") as handle:
        json.dump(daten, handle, ensure_ascii=False, indent=2)


def buch_in_bibliothek_registrieren(
    autor: str,
    titel: str,
    lektor_pfad: str,
    analyse_pfad: str,
) -> None:
    """Traegt ein neues Buch in den Bibliotheksindex ein."""
    bibliothek = bibliothek_laden()

    for buch in bibliothek["buecher"]:
        if buch["autor"] == autor and buch["titel"] == titel:
            print(f"  Buch bereits im Index: {autor} - {titel}")
            return

    kurzbeschreibung = ""
    if os.path.exists(lektor_pfad):
        with open(lektor_pfad, "r", encoding="utf-8") as handle:
            inhalt = handle.read()
        start = inhalt.find("## 3. Kapitelzusammenfassungen")
        if start > 0:
            kurzbeschreibung = inhalt[start : start + 400].strip()
        else:
            kurzbeschreibung = inhalt[:400].strip()

    eintrag = {
        "autor": autor,
        "titel": titel,
        "analysiert_am": str(date.today()),
        "lektor_pfad": lektor_pfad,
        "inhaltsanalyse_pfad": analyse_pfad,
        "kurzbeschreibung": (
            kurzbeschreibung[:300] + "..."
            if len(kurzbeschreibung) > 300
            else kurzbeschreibung
        ),
    }

    bibliothek["buecher"].append(eintrag)
    bibliothek_speichern(bibliothek)
    print(f"  Buch im Index registriert: {autor} - {titel}")
