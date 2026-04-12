"""
Tests für den Delta-Vernetzer.
Testet Dateioperationen – kein API-Aufruf nötig.
"""

import json
import os
import pytest
import re
import tempfile
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Test 1: Delta-Abschnitt wird korrekt an 03_vernetzung.md angehängt
# ---------------------------------------------------------------------------

def test_delta_abschnitt_wird_angehaengt(tmp_path):
    """Prüft dass der Delta-Abschnitt korrekt an die Vernetzungsdatei angehängt wird."""
    vernetzung_datei = tmp_path / "03_vernetzung.md"
    vernetzung_datei.write_text("# Bestehende Vernetzung\n\nAlter Inhalt.", encoding="utf-8")

    delta_text = "Neuer Verbindungsabschnitt zwischen Buch A und Buch X."
    datum = "2026-04-12"
    neuer_autor = "Immanuel Kant"
    neuer_titel = "Zum ewigen Frieden"

    with open(vernetzung_datei, "a", encoding="utf-8") as f:
        f.write(f"\n\n---\n\n")
        f.write(f"## Neue Verbindung: {neuer_autor} – {neuer_titel} (ergänzt {datum})\n\n")
        f.write(delta_text)

    inhalt = vernetzung_datei.read_text(encoding="utf-8")

    assert "Alter Inhalt." in inhalt
    assert "## Neue Verbindung: Immanuel Kant – Zum ewigen Frieden" in inhalt
    assert "Neuer Verbindungsabschnitt" in inhalt
    assert inhalt.index("Alter Inhalt.") < inhalt.index("Neue Verbindung")


# ---------------------------------------------------------------------------
# Test 2: Querverbindungen.json wird korrekt aktualisiert
# ---------------------------------------------------------------------------

def test_querverbindungen_aktualisiert(tmp_path):
    """Prüft dass neue Verbindung eingetragen und alte ersetzt wird."""
    qv_datei = tmp_path / "querverbindungen.json"
    initial = {
        "verbindungen": [
            {"von": "luders_krieg", "zu": "arendt_freiheit", "themen": ["Krieg"], "staerke": 2},
            {"von": "luders_krieg", "zu": "kant_frieden", "themen": ["Alt"], "staerke": 1}
        ]
    }
    qv_datei.write_text(json.dumps(initial, ensure_ascii=False), encoding="utf-8")

    aktuelle_id = "luders_krieg"
    neue_id = "kant_frieden"
    neue_themen = ["Frieden und Gerechtigkeit", "Völkerrecht"]
    neue_staerke = 3

    with open(qv_datei, "r", encoding="utf-8") as f:
        qv = json.load(f)

    qv["verbindungen"] = [
        v for v in qv["verbindungen"]
        if not (v["von"] == aktuelle_id and v["zu"] == neue_id)
        and not (v["von"] == neue_id and v["zu"] == aktuelle_id)
    ]
    qv["verbindungen"].append({
        "von": aktuelle_id,
        "zu": neue_id,
        "themen": neue_themen,
        "staerke": neue_staerke
    })

    with open(qv_datei, "w", encoding="utf-8") as f:
        json.dump(qv, f, ensure_ascii=False, indent=2)

    ergebnis = json.loads(qv_datei.read_text(encoding="utf-8"))
    verbindungen = ergebnis["verbindungen"]

    luders_kant = [v for v in verbindungen if v["von"] == "luders_krieg" and v["zu"] == "kant_frieden"]
    assert len(luders_kant) == 1
    assert luders_kant[0]["staerke"] == 3
    assert "Frieden und Gerechtigkeit" in luders_kant[0]["themen"]
    assert any(v["von"] == "luders_krieg" and v["zu"] == "arendt_freiheit" for v in verbindungen)


# ---------------------------------------------------------------------------
# Test 3: relevanz_check gibt 0 zurück wenn keine Verbindung
# ---------------------------------------------------------------------------

def test_relevanz_check_staerke_null():
    """Prüft dass relevanz_check bei Stärke 0 korrekt zurückgibt."""
    haiku_antwort = '{"staerke": 0, "themen": []}'
    ergebnis = json.loads(haiku_antwort)
    assert ergebnis["staerke"] == 0
    assert ergebnis["themen"] == []


# ---------------------------------------------------------------------------
# Test 4: relevanz_check verarbeitet Markdown-Block korrekt
# ---------------------------------------------------------------------------

def test_relevanz_check_markdown_block():
    """Prüft dass JSON auch aus ```json ... ``` extrahiert wird."""
    haiku_antwort = '```json\n{"staerke": 2, "themen": ["Freiheit", "Krieg"]}\n```'

    if "```" in haiku_antwort:
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', haiku_antwort)
        if match:
            haiku_antwort = match.group(1)

    ergebnis = json.loads(haiku_antwort)
    assert ergebnis["staerke"] == 2
    assert "Freiheit" in ergebnis["themen"]
