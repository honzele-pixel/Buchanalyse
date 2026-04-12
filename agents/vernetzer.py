"""
Agent 3: Der Vernetzer
Findet Querverbindungen zwischen dem aktuellen Buch und allen anderen
bereits analysierten Büchern in der Bibliothek.

WICHTIG: Dieser Agent entfaltet sein volles Potenzial erst wenn mehrere
Bücher analysiert wurden. Mit jedem neuen Buch wird er mächtiger.

Ergebnis: analysen/<Autor>/<Buch>/03_vernetzung.md
         + Update von bibliothek/index.json
"""

import asyncio
import os
import re
import sys
import json
from datetime import date
from dotenv import load_dotenv
import anthropic
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import AssistantMessage, TextBlock, ResultMessage

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

BIBLIOTHEK_INDEX      = r"E:\Claude_Projekte\Buchanalysen\bibliothek\index.json"
QUERVERBINDUNGEN_JSON = r"E:\Claude_Projekte\Buchanalysen\bibliothek\querverbindungen.json"
ANALYSEN_DIR          = r"E:\Claude_Projekte\Buchanalysen\analysen"


SYSTEM_PROMPT = """Du bist ein hochspezialisierter Literaturwissenschaftler und Ideenhistoriker.

Du bekommst:
1. Die vollständige Analyse eines aktuellen Buches (Lektor + Inhaltsanalyse)
2. Eine Übersicht aller bereits analysierten Bücher im Archiv (mit Kurzbeschreibungen)
3. Wo vorhanden: die Analysen der anderen Bücher

Deine Aufgabe: Vernetzungsanalyse

---

## 1. THEMATISCHE QUERVERBINDUNGEN
Welche Themen, Konzepte oder historischen Ereignisse tauchen in mehreren Büchern auf?
Format: Thema → Buch A sagt X, Buch B sagt Y → Gemeinsamkeit/Unterschied

## 2. IDEOLOGISCHE VERWANDTSCHAFTEN
Welche Autoren teilen dasselbe Weltbild? Wo ergänzen sie sich?
Wo widersprechen sie sich – und warum ist das interessant?

## 3. ARGUMENTATIVE BRÜCKEN
Welche These aus Buch A wird durch Buch B bestätigt, erweitert oder widerlegt?
Konkrete Beispiele mit Seitenangaben wo möglich.

## 4. EMPFOHLENE LESEKOMBINATIONEN
Welche Bücher sollte man gemeinsam lesen um ein Thema vollständig zu verstehen?
Begründung: Was leistet jedes Buch das das andere nicht kann?

## 5. WEISSE FLECKEN IM ARCHIV
Welche Perspektiven fehlen noch im Archiv?
Welche Bücher würden die Sammlung sinnvoll ergänzen?

---

HINWEIS: Wenn das Archiv noch wenige Bücher enthält, konzentriere dich auf
die Verbindungen die bereits möglich sind – und skizziere welche Verbindungen
mit zukünftigen Büchern entstehen könnten.

Sprache: Deutsch. Ton: analytisch, präzise, intellektuell anspruchsvoll."""


def buch_netz_id(autor: str, titel: str) -> str:
    """Konsistente Netz-ID aus Autor-Nachname + erstem Titel-Wort (>3 Zeichen)."""
    def slug(s):
        for a, b in [('ü','u'),('ä','a'),('ö','o'),('ß','ss')]:
            s = s.replace(a, b)
        return re.sub(r'[^a-z0-9]', '', s.lower())
    nachname = slug(autor.split()[-1])
    woerter = [w for w in titel.split() if len(w) > 3]
    titelwort = slug(woerter[0]) if woerter else slug(titel.split()[0])
    return f"{nachname}_{titelwort}"


def verbindungen_aktualisieren(autor: str, titel: str, vernetzung_text: str) -> None:
    """Extrahiert strukturierte Verbindungen aus dem Vernetzungstext und aktualisiert querverbindungen.json."""
    bibliothek = bibliothek_laden()
    aktuelle_id = buch_netz_id(autor, titel)

    id_liste = "\n".join([
        f"- {buch_netz_id(b['autor'], b['titel'])}: {b['autor']} – {b['titel']}"
        for b in bibliothek["buecher"]
        if not (b["autor"] == autor and b["titel"] == titel)
    ])

    prompt = f"""Du hast gerade eine Vernetzungsanalyse für "{autor}: {titel}" erstellt.
Extrahiere alle Verbindungen zu anderen Büchern als strukturiertes JSON.

Aktuelle Buch-ID: {aktuelle_id}

Verfügbare andere Buch-IDs:
{id_liste}

Gib NUR ein gültiges JSON-Objekt zurück, absolut kein anderer Text:
{{
  "verbindungen": [
    {{"von": "{aktuelle_id}", "zu": "<andere_buch_id>", "themen": ["Thema 1", "Thema 2"], "staerke": 2}}
  ]
}}

Stärke-Skala: 1=schwach (1 Thema), 2=mittel (2 Themen), 3=stark (3+ Themen oder enger inhaltlicher Bezug)

Vernetzungsanalyse:
{vernetzung_text[:8000]}"""

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    antwort = response.content[0].text.strip()

    # JSON aus Markdown-Block extrahieren falls nötig
    if "```" in antwort:
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', antwort)
        if match:
            antwort = match.group(1)

    neue_verbindungen = json.loads(antwort)["verbindungen"]

    # Existierende Verbindungen laden
    with open(QUERVERBINDUNGEN_JSON, "r", encoding="utf-8") as f:
        querverbindungen = json.load(f)

    # Alte Verbindungen dieses Buches entfernen (sauber ersetzen)
    querverbindungen["verbindungen"] = [
        v for v in querverbindungen["verbindungen"]
        if v["von"] != aktuelle_id and v["zu"] != aktuelle_id
    ]

    # Neue Verbindungen eintragen
    querverbindungen["verbindungen"].extend(neue_verbindungen)

    with open(QUERVERBINDUNGEN_JSON, "w", encoding="utf-8") as f:
        json.dump(querverbindungen, f, ensure_ascii=False, indent=2)

    print(f"  Querverbindungen aktualisiert: {len(neue_verbindungen)} Verbindungen für '{aktuelle_id}'")


def bibliothek_laden() -> dict:
    """Lädt den aktuellen Stand des Bibliotheksindex."""
    with open(BIBLIOTHEK_INDEX, "r", encoding="utf-8") as f:
        return json.load(f)


def bibliothek_speichern(daten: dict) -> None:
    """Speichert den aktualisierten Bibliotheksindex."""
    with open(BIBLIOTHEK_INDEX, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)


def buch_in_bibliothek_registrieren(autor: str, titel: str, lektor_pfad: str, analyse_pfad: str) -> None:
    """Trägt ein neues Buch in den Bibliotheksindex ein."""
    bibliothek = bibliothek_laden()

    # Prüfen ob bereits vorhanden
    for buch in bibliothek["buecher"]:
        if buch["autor"] == autor and buch["titel"] == titel:
            print(f"  Buch bereits im Index: {autor} – {titel}")
            return

    # Kurzbeschreibung aus Lektor extrahieren (erste 500 Zeichen des Inhalts)
    kurzbeschreibung = ""
    if os.path.exists(lektor_pfad):
        with open(lektor_pfad, "r", encoding="utf-8") as f:
            inhalt = f.read()
            # Erste Kapitelzusammenfassung als Kurzbeschreibung
            start = inhalt.find("## 3. Kapitelzusammenfassungen")
            if start > 0:
                kurzbeschreibung = inhalt[start:start+400].strip()
            else:
                kurzbeschreibung = inhalt[:400].strip()

    eintrag = {
        "autor": autor,
        "titel": titel,
        "analysiert_am": str(date.today()),
        "lektor_pfad": lektor_pfad,
        "inhaltsanalyse_pfad": analyse_pfad,
        "kurzbeschreibung": kurzbeschreibung[:300] + "..." if len(kurzbeschreibung) > 300 else kurzbeschreibung
    }

    bibliothek["buecher"].append(eintrag)
    bibliothek_speichern(bibliothek)
    print(f"  Buch im Index registriert: {autor} – {titel}")


def andere_analysen_laden(aktueller_autor: str, aktueller_titel: str) -> list[dict]:
    """Lädt alle anderen bereits analysierten Bücher."""
    bibliothek = bibliothek_laden()
    andere = []

    for buch in bibliothek["buecher"]:
        if buch["autor"] == aktueller_autor and buch["titel"] == aktueller_titel:
            continue  # Aktuelles Buch überspringen

        buch_info = {
            "autor": buch["autor"],
            "titel": buch["titel"],
            "lektor": "",
            "analyse": ""
        }

        # Lektor-Aufbereitung laden (gekürzt)
        if os.path.exists(buch["lektor_pfad"]):
            with open(buch["lektor_pfad"], "r", encoding="utf-8") as f:
                inhalt = f.read()
                buch_info["lektor"] = inhalt[:8000]  # Erste 8000 Zeichen

        # Inhaltsanalyse laden (gekürzt)
        if os.path.exists(buch.get("inhaltsanalyse_pfad", "")):
            with open(buch["inhaltsanalyse_pfad"], "r", encoding="utf-8") as f:
                inhalt = f.read()
                buch_info["analyse"] = inhalt[:8000]

        andere.append(buch_info)

    return andere


async def vernetzer_analysieren(
    autor: str,
    titel: str,
    lektor_pfad: str,
    inhaltsanalyse_pfad: str,
    ausgabe_pfad: str
) -> None:
    """Vernetzt das aktuelle Buch mit dem bestehenden Archiv."""

    print(f"\n{'='*60}")
    print(f"VERNETZER startet: {autor} – {titel}")
    print(f"{'='*60}\n")

    # 1. Aktuelles Buch im Index registrieren
    print("Schritt 1: Buch in Bibliothek registrieren...")
    buch_in_bibliothek_registrieren(autor, titel, lektor_pfad, inhaltsanalyse_pfad)

    # 2. Aktuelle Analysen laden
    print("Schritt 2: Aktuelle Analysen laden...")
    with open(lektor_pfad, "r", encoding="utf-8") as f:
        lektor_text = f.read()
    with open(inhaltsanalyse_pfad, "r", encoding="utf-8") as f:
        analyse_text = f.read()
    print(f"  Lektor: {len(lektor_text):,} Zeichen")
    print(f"  Inhaltsanalyse: {len(analyse_text):,} Zeichen")

    # 3. Andere Bücher aus dem Archiv laden
    print("Schritt 3: Archiv durchsuchen...")
    andere_buecher = andere_analysen_laden(autor, titel)
    print(f"  {len(andere_buecher)} weitere Bücher im Archiv\n")

    # Archiv-Übersicht für den Prompt erstellen
    if andere_buecher:
        archiv_text = "\n\n".join([
            f"### {b['autor']}: {b['titel']}\n\n**Lektor-Auszug:**\n{b['lektor'][:3000]}\n\n**Analyse-Auszug:**\n{b['analyse'][:3000]}"
            for b in andere_buecher
        ])
    else:
        archiv_text = "Das Archiv enthält noch keine weiteren Bücher. Dies ist die erste Analyse.\nSkizziere welche Verbindungen mit zukünftigen Büchern zu erwarten sind, basierend auf den Themen dieses Buches."

    bibliothek = bibliothek_laden()
    archiv_uebersicht = "\n".join([
        f"- {b['autor']}: {b['titel']} (analysiert: {b['analysiert_am']})"
        for b in bibliothek["buecher"]
    ])

    prompt = f"""Aktuelles Buch zur Vernetzung:
**{autor}: {titel}**

--- LEKTOR-AUFBEREITUNG (aktuelles Buch) ---
{lektor_text[:15000]}

--- INHALTSANALYSE (aktuelles Buch) ---
{analyse_text[:10000]}

--- ARCHIV-ÜBERSICHT ---
Bisher analysierte Bücher:
{archiv_uebersicht}

--- ANDERE BÜCHER IM ARCHIV ---
{archiv_text}

Bitte erstelle nun die Vernetzungsanalyse."""

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=[],
        permission_mode="acceptEdits",
        max_turns=3,
    )

    print("Vernetzer arbeitet...\n")
    print("-" * 60)

    ergebnis_teile = []
    kosten = 0.0

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="", flush=True)
                    ergebnis_teile.append(block.text)
        elif isinstance(message, ResultMessage):
            if message.is_error:
                print(f"\n[Fehler]: {message.subtype}")
            elif message.total_cost_usd is not None:
                kosten = message.total_cost_usd
                print(f"\n\n[Kosten: ${kosten:.4f} | Durchläufe: {message.num_turns}]")

    print("\n" + "-" * 60)

    # Ergebnis speichern
    ergebnis = "".join(ergebnis_teile)
    archiv_stand = f"{len(bibliothek['buecher'])} Buch/Bücher im Archiv"

    os.makedirs(os.path.dirname(ausgabe_pfad), exist_ok=True)
    with open(ausgabe_pfad, "w", encoding="utf-8") as f:
        f.write(f"# Vernetzungsanalyse: {titel}\n\n")
        f.write(f"**Autor:** {autor}  \n")
        f.write(f"**Archivstand:** {archiv_stand}  \n")
        f.write(f"**Analysiert am:** {date.today()}  \n\n")
        f.write("> Hinweis: Diese Analyse wächst mit jedem neuen Buch im Archiv.\n\n")
        f.write("---\n\n")
        f.write(ergebnis)

    print(f"\nGespeichert: {ausgabe_pfad}")

    # Strukturierte Verbindungen für das Wissensnetz extrahieren
    print("Extrahiere strukturierte Verbindungen für Wissensnetz...")
    try:
        verbindungen_aktualisieren(autor, titel, ergebnis)
    except Exception as e:
        print(f"  [Warnung] Verbindungen konnten nicht extrahiert werden: {e}")

    print(f"{'='*60}\n")


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
) -> bool:
    """Ergänzt 03_vernetzung.md eines bestehenden Buches um eine neue Verbindung.

    Phase 1 (Haiku): Relevanz-Check – bei Stärke 0 wird nichts geschrieben.
    Phase 2 (Sonnet): Delta-Abschnitt schreiben und anhängen.
    """
    buch_a_autor = bestehendes_buch["autor"]
    buch_a_titel = bestehendes_buch["titel"]

    # Texte laden
    try:
        with open(bestehendes_buch["lektor_pfad"], "r", encoding="utf-8") as f:
            buch_a_lektor = f.read()
        inhaltsanalyse_pfad = bestehendes_buch.get("inhaltsanalyse_pfad", "")
        if inhaltsanalyse_pfad and os.path.exists(inhaltsanalyse_pfad):
            with open(inhaltsanalyse_pfad, "r", encoding="utf-8") as f:
                buch_a_analyse = f.read()
        else:
            buch_a_analyse = ""
        with open(neuer_lektor_pfad, "r", encoding="utf-8") as f:
            buch_x_lektor = f.read()
        with open(neue_inhaltsanalyse_pfad, "r", encoding="utf-8") as f:
            buch_x_analyse = f.read()
    except FileNotFoundError as e:
        print(f"    [Warnung] Datei nicht gefunden: {e} – wird übersprungen.")
        return False

    # Phase 1: Relevanz-Check (Haiku – schnell & günstig)
    print(f"    Relevanz-Check (Haiku): {buch_a_autor} – {buch_a_titel}...")
    try:
        relevanz = relevanz_check(
            buch_a_autor, buch_a_titel, buch_a_lektor,
            neuer_autor, neuer_titel, buch_x_lektor,
        )
    except Exception as e:
        print(f"    [Warnung] Relevanz-Check fehlgeschlagen: {e} – wird übersprungen.")
        return False

    if relevanz["staerke"] == 0:
        print(f"    → Keine relevante Verbindung – wird übersprungen.")
        return False

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

    if not delta_text.strip():
        print(f"    [Warnung] Kein Inhalt vom Sonnet erhalten – wird übersprungen.")
        return False

    # An 03_vernetzung.md anhängen
    vernetzung_pfad = os.path.join(os.path.dirname(bestehendes_buch["lektor_pfad"]), "03_vernetzung.md")

    if not os.path.exists(vernetzung_pfad):
        print(f"    [Warnung] 03_vernetzung.md nicht gefunden: {vernetzung_pfad} – wird übersprungen.")
        return False

    with open(vernetzung_pfad, "a", encoding="utf-8") as f:
        f.write(f"\n\n---\n\n")
        f.write(f"## Neue Verbindung: {neuer_autor} – {neuer_titel} (ergänzt {date.today()})\n\n")
        f.write(delta_text)

    print(f"    → Abschnitt angehängt: {vernetzung_pfad}")

    # querverbindungen.json aktualisieren
    try:
        aktuelle_id = buch_netz_id(buch_a_autor, buch_a_titel)
        neue_id = buch_netz_id(neuer_autor, neuer_titel)

        with open(QUERVERBINDUNGEN_JSON, "r", encoding="utf-8") as f:
            querverbindungen = json.load(f)

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
    except Exception as e:
        print(f"    [Warnung] Querverbindungen konnten nicht aktualisiert werden: {e}")

    return True


if __name__ == "__main__":
    asyncio.run(vernetzer_analysieren(
        autor             = "Michael Lüders",
        titel             = "Krieg ohne Ende",
        lektor_pfad       = r"E:\Claude_Projekte\Buchanalysen\analysen\Michael_Luders\Krieg_ohne_Ende\01_lektor.md",
        inhaltsanalyse_pfad = r"E:\Claude_Projekte\Buchanalysen\analysen\Michael_Luders\Krieg_ohne_Ende\02_inhaltsanalyse.md",
        ausgabe_pfad      = r"E:\Claude_Projekte\Buchanalysen\analysen\Michael_Luders\Krieg_ohne_Ende\03_vernetzung.md",
    ))
