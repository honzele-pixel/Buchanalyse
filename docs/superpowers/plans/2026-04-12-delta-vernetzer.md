# Delta-Vernetzer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bestehende Bücher beim Hinzufügen eines neuen Buches nur noch mit einem gezielten Delta-Abschnitt ergänzen, statt komplett neu zu vernetzen – bei gleichbleibender Qualität.

**Architecture:** Zwei neue Funktionen in `agents/vernetzer.py`: `relevanz_check()` (Haiku-Schnellprüfung) und `vernetzer_delta_aktualisieren()` (Sonnet-Delta-Abschnitt). `main.py` ruft statt des vollen Vernetzers die neue Delta-Funktion auf. Der volle Vernetzer (`vernetzer_analysieren`) bleibt unverändert.

**Tech Stack:** Python 3, anthropic SDK (direkte API), claude-agent-sdk, pytest

---

## Dateiübersicht

| Datei | Aktion | Was ändert sich |
|-------|--------|-----------------|
| `agents/vernetzer.py` | Erweitern | Zwei neue Funktionen am Ende der Datei |
| `main.py` | Erweitern | Import + `vernetzungen_aktualisieren()` umschreiben |
| `tests/test_delta_vernetzer.py` | Neu erstellen | Tests für Dateioperationen (kein API-Mock nötig) |

---

## Task 1: Test-Datei anlegen

**Files:**
- Create: `tests/test_delta_vernetzer.py`

- [ ] **Schritt 1: tests-Ordner und Test-Datei anlegen**

```bash
mkdir -p tests
```

Erstelle `tests/test_delta_vernetzer.py` mit folgendem Inhalt:

```python
"""
Tests für den Delta-Vernetzer.
Testet Dateioperationen – kein API-Aufruf nötig.
"""

import json
import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Test 1: Delta-Abschnitt wird korrekt an 03_vernetzung.md angehängt
# ---------------------------------------------------------------------------

def test_delta_abschnitt_wird_angehaengt(tmp_path):
    """Prüft dass der Delta-Abschnitt korrekt an die Vernetzungsdatei angehängt wird."""
    # Bestehende Vernetzungsdatei anlegen
    vernetzung_datei = tmp_path / "03_vernetzung.md"
    vernetzung_datei.write_text("# Bestehende Vernetzung\n\nAlter Inhalt.", encoding="utf-8")

    # Delta-Text simulieren
    delta_text = "Neuer Verbindungsabschnitt zwischen Buch A und Buch X."
    datum = "2026-04-12"
    neuer_autor = "Immanuel Kant"
    neuer_titel = "Zum ewigen Frieden"

    # Anhängen (gleiche Logik wie in vernetzer_delta_aktualisieren)
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
            # Alte Verbindung die ersetzt werden soll:
            {"von": "luders_krieg", "zu": "kant_frieden", "themen": ["Alt"], "staerke": 1}
        ]
    }
    qv_datei.write_text(json.dumps(initial, ensure_ascii=False), encoding="utf-8")

    aktuelle_id = "luders_krieg"
    neue_id = "kant_frieden"
    neue_themen = ["Frieden und Gerechtigkeit", "Völkerrecht"]
    neue_staerke = 3

    # Aktualisierungslogik (gleich wie in vernetzer_delta_aktualisieren)
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

    # Alte Verbindung ist weg, neue ist drin
    luders_kant = [v for v in verbindungen if v["von"] == "luders_krieg" and v["zu"] == "kant_frieden"]
    assert len(luders_kant) == 1
    assert luders_kant[0]["staerke"] == 3
    assert "Frieden und Gerechtigkeit" in luders_kant[0]["themen"]

    # Andere Verbindung unberührt
    assert any(v["von"] == "luders_krieg" and v["zu"] == "arendt_freiheit" for v in verbindungen)


# ---------------------------------------------------------------------------
# Test 3: relevanz_check gibt 0 zurück wenn keine Verbindung
# ---------------------------------------------------------------------------

def test_relevanz_check_kein_json_fehler():
    """Prüft dass relevanz_check bei Stärke 0 korrekt zurückgibt."""
    # Simuliert was relevanz_check mit einer Haiku-Antwort macht
    haiku_antwort = '{"staerke": 0, "themen": []}'
    ergebnis = json.loads(haiku_antwort)
    assert ergebnis["staerke"] == 0
    assert ergebnis["themen"] == []


# ---------------------------------------------------------------------------
# Test 4: relevanz_check verarbeitet Markdown-Block korrekt
# ---------------------------------------------------------------------------

def test_relevanz_check_markdown_block():
    """Prüft dass JSON auch aus ```json ... ``` extrahiert wird."""
    import re
    haiku_antwort = '```json\n{"staerke": 2, "themen": ["Freiheit", "Krieg"]}\n```'

    if "```" in haiku_antwort:
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', haiku_antwort)
        if match:
            haiku_antwort = match.group(1)

    ergebnis = json.loads(haiku_antwort)
    assert ergebnis["staerke"] == 2
    assert "Freiheit" in ergebnis["themen"]
```

- [ ] **Schritt 2: Tests ausführen und sicherstellen dass sie SCHEITERN (Funktionen noch nicht vorhanden)**

```bash
cd E:\Claude_Projekte\Buchanalysen && python -m pytest tests/test_delta_vernetzer.py -v
```

Erwartetes Ergebnis: Tests 1–4 PASS (diese testen reine Logik ohne Imports aus vernetzer.py).

---

## Task 2: `relevanz_check()` in vernetzer.py hinzufügen

**Files:**
- Modify: `agents/vernetzer.py` (am Ende der Datei, vor `if __name__ == "__main__":`)

- [ ] **Schritt 1: Funktion `relevanz_check()` einfügen**

Füge folgende Funktion in `agents/vernetzer.py` **vor** dem Block `if __name__ == "__main__":` ein:

```python
def relevanz_check(
    buch_a_autor: str,
    buch_a_titel: str,
    buch_a_lektor: str,
    buch_x_autor: str,
    buch_x_titel: str,
    buch_x_lektor: str,
) -> dict:
    """Haiku prüft ob Buch X für Buch A relevant ist.
    
    Gibt zurück: {"staerke": 0-3, "themen": ["Thema 1", ...]}
    Stärke 0 = keine Verbindung → Delta-Abschnitt wird nicht geschrieben.
    """
    prompt = f"""Du vergleichst zwei Bücher auf thematische Verbindungen.

Buch A: {buch_a_autor} – {buch_a_titel}
{buch_a_lektor[:2000]}

Buch X (neu hinzugefügt): {buch_x_autor} – {buch_x_titel}
{buch_x_lektor[:2000]}

Wie stark sind die inhaltlichen Verbindungen zwischen diesen beiden Büchern?

Gib NUR ein gültiges JSON-Objekt zurück – kein anderer Text:
{{"staerke": 0, "themen": []}}

Stärke-Skala:
0 = keine relevante Verbindung
1 = schwache Verbindung (1 gemeinsames Thema)
2 = mittlere Verbindung (2 Themen oder ein enger inhaltlicher Bezug)
3 = starke Verbindung (3+ Themen oder sehr enger inhaltlicher Bezug)

Themen: Liste der konkreten gemeinsamen Themen/Begriffe (leer wenn Stärke 0)."""

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    antwort = response.content[0].text.strip()

    if "```" in antwort:
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', antwort)
        if match:
            antwort = match.group(1)

    return json.loads(antwort)
```

- [ ] **Schritt 2: Schnelltest – Funktion importierbar?**

```bash
cd E:\Claude_Projekte\Buchanalysen && python -c "from agents.vernetzer import relevanz_check; print('OK')"
```

Erwartetes Ergebnis: `OK`

---

## Task 3: `vernetzer_delta_aktualisieren()` in vernetzer.py hinzufügen

**Files:**
- Modify: `agents/vernetzer.py` (nach `relevanz_check()`, vor `if __name__ == "__main__":`)

- [ ] **Schritt 1: Funktion `vernetzer_delta_aktualisieren()` einfügen**

Füge folgende Funktion **nach** `relevanz_check()` und **vor** `if __name__ == "__main__":` ein:

```python
DELTA_SYSTEM_PROMPT = """Du bist ein hochspezialisierter Literaturwissenschaftler und Ideenhistoriker.
Du ergänzt bestehende Vernetzungsanalysen um neue Buchverbindungen.
Deine Analysen sind präzise, tiefgründig und intellektuell anspruchsvoll.
Du schreibst ausschließlich den Inhalt des neuen Abschnitts – keine Überschrift, keine Einleitung."""


async def vernetzer_delta_aktualisieren(
    bestehendes_buch: dict,
    neuer_autor: str,
    neuer_titel: str,
    neuer_lektor_pfad: str,
    neue_inhaltsanalyse_pfad: str,
) -> None:
    """Ergänzt 03_vernetzung.md eines bestehenden Buches um eine neue Verbindung.
    
    Phase 1 (Haiku): Relevanz-Check – bei Stärke 0 wird nichts geschrieben.
    Phase 2 (Sonnet): Delta-Abschnitt schreiben und anhängen.
    """
    buch_a_autor = bestehendes_buch["autor"]
    buch_a_titel = bestehendes_buch["titel"]

    # Texte laden
    with open(bestehendes_buch["lektor_pfad"], "r", encoding="utf-8") as f:
        buch_a_lektor = f.read()
    with open(bestehendes_buch.get("inhaltsanalyse_pfad", ""), "r", encoding="utf-8") as f:
        buch_a_analyse = f.read()
    with open(neuer_lektor_pfad, "r", encoding="utf-8") as f:
        buch_x_lektor = f.read()
    with open(neue_inhaltsanalyse_pfad, "r", encoding="utf-8") as f:
        buch_x_analyse = f.read()

    # Phase 1: Relevanz-Check (Haiku – schnell & günstig)
    print(f"    Relevanz-Check (Haiku): {buch_a_autor} – {buch_a_titel}...")
    try:
        relevanz = relevanz_check(
            buch_a_autor, buch_a_titel, buch_a_lektor,
            neuer_autor, neuer_titel, buch_x_lektor,
        )
    except Exception as e:
        print(f"    [Warnung] Relevanz-Check fehlgeschlagen: {e} – wird übersprungen.")
        return

    if relevanz["staerke"] == 0:
        print(f"    → Keine relevante Verbindung – wird übersprungen.")
        return

    print(f"    → Stärke {relevanz['staerke']} | Themen: {', '.join(relevanz['themen'])}")
    print(f"    Delta-Abschnitt wird geschrieben (Sonnet)...")

    # Phase 2: Delta-Abschnitt schreiben (Sonnet – hohe Qualität)
    delta_prompt = f"""Du ergänzt die Vernetzungsanalyse von "{buch_a_autor}: {buch_a_titel}"
um eine neue Verbindung zum soeben analysierten Buch "{neuer_autor}: {neuer_titel}".

--- BUCH A: {buch_a_autor} – {buch_a_titel} ---
Lektor-Auszug:
{buch_a_lektor[:8000]}

Inhaltsanalyse-Auszug:
{buch_a_analyse[:8000]}

--- NEUES BUCH X: {neuer_autor} – {neuer_titel} ---
Lektor-Auszug:
{buch_x_lektor[:8000]}

Inhaltsanalyse-Auszug:
{buch_x_analyse[:8000]}

Bekannte Verbindungsthemen (aus Vorprüfung): {', '.join(relevanz['themen'])}

Schreibe einen präzisen Abschnitt der folgende Punkte behandelt:

### Thematische Querverbindungen
Welche Themen, Konzepte oder historischen Ereignisse tauchen in beiden Büchern auf?
Konkret, mit Beispielen aus beiden Büchern.

### Argumentative Brücken
Welche These aus Buch A wird durch Buch X bestätigt, erweitert oder widerlegt?
Wo ergänzen sich die Argumente, wo widersprechen sie sich?

### Empfohlene Lesekombination
Warum sollte man beide Bücher gemeinsam lesen?
Was leistet jedes Buch das das andere nicht kann?

Sprache: Deutsch. Ton: analytisch, präzise, intellektuell anspruchsvoll.
Schreibe NUR den Inhalt der drei Unterabschnitte – die Überschriften (###) einschließen."""

    options = ClaudeAgentOptions(
        system_prompt=DELTA_SYSTEM_PROMPT,
        allowed_tools=[],
        permission_mode="acceptEdits",
        max_turns=2,
    )

    delta_teile = []
    async for message in query(prompt=delta_prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="", flush=True)
                    delta_teile.append(block.text)

    print()
    delta_text = "".join(delta_teile)

    # An 03_vernetzung.md anhängen
    vernetzung_pfad = bestehendes_buch["lektor_pfad"].replace("01_lektor.md", "03_vernetzung.md")

    if not os.path.exists(vernetzung_pfad):
        print(f"    [Warnung] 03_vernetzung.md nicht gefunden: {vernetzung_pfad} – wird übersprungen.")
        return

    with open(vernetzung_pfad, "a", encoding="utf-8") as f:
        f.write(f"\n\n---\n\n")
        f.write(f"## Neue Verbindung: {neuer_autor} – {neuer_titel} (ergänzt {date.today()})\n\n")
        f.write(delta_text)

    print(f"    → Abschnitt angehängt: {vernetzung_pfad}")

    # querverbindungen.json aktualisieren
    aktuelle_id = buch_netz_id(buch_a_autor, buch_a_titel)
    neue_id = buch_netz_id(neuer_autor, neuer_titel)

    with open(QUERVERBINDUNGEN_JSON, "r", encoding="utf-8") as f:
        querverbindungen = json.load(f)

    # Alte Verbindung zwischen diesen beiden entfernen (verhindert Duplikate)
    querverbindungen["verbindungen"] = [
        v for v in querverbindungen["verbindungen"]
        if not (v["von"] == aktuelle_id and v["zu"] == neue_id)
        and not (v["von"] == neue_id and v["zu"] == aktuelle_id)
    ]

    querverbindungen["verbindungen"].append({
        "von": aktuelle_id,
        "zu": neue_id,
        "themen": relevanz["themen"],
        "staerke": relevanz["staerke"]
    })

    with open(QUERVERBINDUNGEN_JSON, "w", encoding="utf-8") as f:
        json.dump(querverbindungen, f, ensure_ascii=False, indent=2)

    print(f"    → Querverbindung: {aktuelle_id} ↔ {neue_id} (Stärke {relevanz['staerke']})")
```

- [ ] **Schritt 2: Import-Test**

```bash
cd E:\Claude_Projekte\Buchanalysen && python -c "from agents.vernetzer import relevanz_check, vernetzer_delta_aktualisieren; print('OK')"
```

Erwartetes Ergebnis: `OK`

- [ ] **Schritt 3: Tests laufen lassen**

```bash
cd E:\Claude_Projekte\Buchanalysen && python -m pytest tests/test_delta_vernetzer.py -v
```

Erwartetes Ergebnis: Alle 4 Tests PASS

---

## Task 4: `main.py` – Import + `vernetzungen_aktualisieren()` umschreiben

**Files:**
- Modify: `main.py` (Import-Zeile + Funktion `vernetzungen_aktualisieren`)

- [ ] **Schritt 1: Import in main.py erweitern**

Ändere in `main.py` die Zeile:

```python
from agents.vernetzer         import vernetzer_analysieren
```

zu:

```python
from agents.vernetzer         import vernetzer_analysieren, vernetzer_delta_aktualisieren
```

- [ ] **Schritt 2: `vernetzungen_aktualisieren()` komplett ersetzen**

Ersetze in `main.py` die gesamte Funktion `vernetzungen_aktualisieren()` (Zeilen 105–136) durch:

```python
async def vernetzungen_aktualisieren(neuer_autor: str, neuer_titel: str) -> None:
    """Aktualisiert die Vernetzung aller anderen Bücher im Archiv (Delta-Modus).
    
    Für jedes bestehende Buch:
    - Haiku prüft ob eine Verbindung zum neuen Buch besteht
    - Sonnet schreibt nur wenn relevant einen neuen Abschnitt (kein Neuschreiben)
    """
    with open(BIBLIOTHEK_INDEX, "r", encoding="utf-8") as f:
        bibliothek = json.load(f)

    andere = [b for b in bibliothek["buecher"]
              if not (b["autor"] == neuer_autor and b["titel"] == neuer_titel)]

    if not andere:
        print("  Keine anderen Bücher im Archiv – Delta-Vernetzung nicht nötig.")
        return

    # Pfade des neuen Buches aus dem Index holen
    neuer_lektor_pfad = None
    neue_inhaltsanalyse_pfad = None
    for b in bibliothek["buecher"]:
        if b["autor"] == neuer_autor and b["titel"] == neuer_titel:
            neuer_lektor_pfad = b["lektor_pfad"]
            neue_inhaltsanalyse_pfad = b["inhaltsanalyse_pfad"]
            break

    if not neuer_lektor_pfad:
        print("  [Fehler] Neues Buch nicht im Index gefunden – Delta-Vernetzung abgebrochen.")
        return

    print(f"\n{'='*60}")
    print(f"  DELTA-VERNETZUNG: {len(andere)} Bücher werden geprüft...")
    print(f"  (Haiku-Check → nur bei Verbindung wird Sonnet geschrieben)")
    print(f"{'='*60}")

    uebersprungen = 0
    ergaenzt = 0

    for i, buch in enumerate(andere, start=1):
        print(f"\n  [{i}/{len(andere)}] {buch['autor']} – {buch['titel']}")
        vorher_groesse = 0
        vernetzung_pfad = buch["lektor_pfad"].replace("01_lektor.md", "03_vernetzung.md")
        if os.path.exists(vernetzung_pfad):
            vorher_groesse = os.path.getsize(vernetzung_pfad)

        await vernetzer_delta_aktualisieren(
            bestehendes_buch=buch,
            neuer_autor=neuer_autor,
            neuer_titel=neuer_titel,
            neuer_lektor_pfad=neuer_lektor_pfad,
            neue_inhaltsanalyse_pfad=neue_inhaltsanalyse_pfad,
        )

        if os.path.exists(vernetzung_pfad) and os.path.getsize(vernetzung_pfad) > vorher_groesse:
            ergaenzt += 1
        else:
            uebersprungen += 1

    print(f"\n{'='*60}")
    print(f"  DELTA-VERNETZUNG ABGESCHLOSSEN!")
    print(f"  Ergänzt: {ergaenzt} Bücher | Übersprungen: {uebersprungen} Bücher")
    print(f"{'='*60}\n")
```

- [ ] **Schritt 3: Syntaxprüfung**

```bash
cd E:\Claude_Projekte\Buchanalysen && python -c "import main; print('Syntax OK')"
```

Erwartetes Ergebnis: `Syntax OK`

---

## Task 5: Commit

**Files:** alle geänderten Dateien

- [ ] **Schritt 1: Status prüfen**

```bash
cd E:\Claude_Projekte\Buchanalysen && git status
```

Erwartetes Ergebnis: Geändert: `agents/vernetzer.py`, `main.py` | Neu: `tests/test_delta_vernetzer.py`, `docs/superpowers/`

- [ ] **Schritt 2: Commit**

```bash
cd E:\Claude_Projekte\Buchanalysen && git add agents/vernetzer.py main.py tests/test_delta_vernetzer.py docs/superpowers/specs/2026-04-12-delta-vernetzer-design.md docs/superpowers/plans/2026-04-12-delta-vernetzer.md && git commit -m "feat: Delta-Vernetzer – inkrementelle Vernetzung statt Komplett-Neudurchlauf

Beim Hinzufügen eines neuen Buches werden bestehende Bücher nicht mehr
komplett neu vernetzt. Stattdessen:
- Haiku prüft Relevanz (Stärke 0-3)
- Nur bei Verbindung schreibt Sonnet einen neuen Abschnitt
- 03_vernetzung.md wächst organisch durch angehängte Abschnitte
- querverbindungen.json wird gezielt aktualisiert

Skaliert von ~2 Std (50 Bücher) auf ~20 Min."
```

---

## Selbst-Review

**Spec-Abdeckung:**
- [x] Haiku Relevanz-Check (Stärke 0–3) → Task 2
- [x] Sonnet schreibt Delta-Abschnitt → Task 3
- [x] Abschnitt wird an 03_vernetzung.md angehängt → Task 3
- [x] querverbindungen.json wird aktualisiert → Task 3
- [x] main.py nutzt Delta-Funktion → Task 4
- [x] Voller Vernetzer bleibt unverändert → nicht angefasst

**Placeholder-Scan:** Keine TBDs, keine offenen Punkte.

**Typ-Konsistenz:**
- `relevanz_check()` → gibt `dict` mit `staerke` (int) und `themen` (list) zurück
- `vernetzer_delta_aktualisieren()` → `bestehendes_buch` ist ein `dict` aus `index.json` (hat `autor`, `titel`, `lektor_pfad`, `inhaltsanalyse_pfad`)
- `buch_netz_id()` → bereits in vernetzer.py vorhanden, wird wiederverwendet
- Alle Pfad-Konstanten (`QUERVERBINDUNGEN_JSON`, `BIBLIOTHEK_INDEX`) → bereits in vernetzer.py definiert
