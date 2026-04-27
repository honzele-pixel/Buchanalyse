"""
Agent 6: Der Sekundärquellen-Analyst

Workflow:
1. Liest 06_index.md (Prioritätsliste mit Sternen) als Startpunkt
2. Liest bereits fertige Einzelanalysen aus 06_sekundaerquellen/
3. Diskutiert interaktiv mit Honzele – von höchster Priorität abwärts
4. Speichert pro Quelle eine eigene Datei (06_autor_jahr.md)
5. Aktualisiert den Index-Status nach jeder Analyse
6. Bietet Wiki-Injektion an (Kopie nach wiki/raw/)

EISERNE REGEL: Nichts wird automatisch gespeichert.
Nur Honzeles explizites 'B' + Bestätigung löst eine Analyse aus.
"""

import asyncio
import os
import re
import shutil
import sys
import json
import tempfile
from datetime import date
from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import AssistantMessage, TextBlock, ResultMessage, SystemPromptFile

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

BIBLIOTHEK_INDEX    = r"E:\Claude_Projekte\Buchanalysen\bibliothek\index.json"
QUALITAETS_REFERENZ = r"E:\Claude_Projekte\Wiki_Honzele\raw\Cockburn_2021_Iron_Triangle_Sekundaeranalyse.md"
WIKI_RAW_DIR        = r"E:\Claude_Projekte\Wiki_Honzele\raw"
SEKUNDAER_ORDNER    = "06_sekundaerquellen"


# ─────────────────────────────────────────────
#  SYSTEM-PROMPTS
# ─────────────────────────────────────────────

SYSTEM_PROMPT_DISKUSSION = """Du bist der Sekundärquellen-Analyst – ein hochspezialisierter Quellenexperte.

## DEIN STARTPUNKT – DER PRIORITÄTS-INDEX:
Wenn ein 06_index.md vorhanden ist, beginne DORT – nicht bei der rohen Quellenliste.
Präsentiere die noch offenen Quellen (Status "→ offen") nach Sternen – höchste zuerst.
Überspringe bereits analysierte Quellen (Status "✓ analysiert").
Wenn kein Index vorhanden ist, analysiere die 05_quellen.md und schlage die 5 wichtigsten vor.

## DEINE EISERNE REGEL – NIEMALS BRECHEN:
Du schreibst KEINEN Bericht. Du erstellst KEINE Datei. Du speicherst NICHTS.
Du diskutierst NUR. Die Entscheidung trifft AUSSCHLIESSLICH Honzele.
Kündige NIEMALS selbst an, einen Bericht zu schreiben.

## WIE DU VORSCHLÄGE MACHST:
Präsentiere 2–3 Quellen auf einmal, kurz und konkret. Beispiel:
"Reich (1933) ★★★★★ – Massenpsychologie des Faschismus: erklärt warum Menschen
Herrschaft nicht nur dulden, sondern aktiv wollen. Ohne ihn bleibt Mausfelds
Gehorsams-These psychologisch unbegründet. Tiefer?"

Dann wartest du auf Honzeles Reaktion. Kein Vortrag, kein Monolog.

## WENN HONZELE TIEFER WILL:
- Was genau argumentiert dieses Werk?
- Welche Lücke in Mausfelds Argumentation füllt es?
- Welche Wiki-Seiten würde es bereichern?
- Verbindung zu Honzeles Kanon (Pleonexia, Melier-Dialog, Hirten-Herden)?

## DEIN STIL:
- Direkt, klar, enthusiastisch aber nicht aufdringlich
- Immer auf Deutsch
- Intellektuell auf Augenhöhe – Honzele ist sehr belesen und analytisch denkend
- Kurze Impulse, dann warten – kein Vortrag halten

## DEINE WISSENSGRUNDLAGE – NUR DIESE:
{kontext}"""


SYSTEM_PROMPT_BERICHT = """Du bist der Sekundärquellen-Analyst.

Erstelle jetzt eine tiefe Einzelanalyse der besprochenen Quelle.
Orientiere dich an der QUALITÄTS-REFERENZ – kopiere sie nicht, erreiche ihre Tiefe.

## STRUKTUR – 3 SCHICHTEN:

### [Autor, Jahr] – [Titel]
**Bibliografische Angabe:** (vollständig aus 05_quellen.md)
**Primärkontext:** Zitiert in: [Autor des analysierten Buches] – [Titel]

---

#### Schicht 1: Was das Werk argumentiert
Worum geht es? Was ist die Kernthese? Welche Methode verwendet der Autor?
(Präzise, 3–5 Absätze – kein oberflächliches Referat)

---

#### Schicht 2: Die Brücke zum Primärwerk
Warum zitiert [Primärautor] dieses Werk? Welche konkrete These stützt es?
Welche Lücke füllt es in der Argumentation des Primärwerks?
Was erklärt das Primärwerk NICHT, was diese Quelle erklärt?

---

#### Schicht 3: Verbindung zu Honzeles Kanon + Wiki-Potenzial
Verbindungen zu: Pleonexia, Melier-Dialog, Hirten-Herden-Metapher, Diagnoselinie
Welche bestehenden Wiki-Seiten würde diese Quelle anreichern?
Welche neuen Wiki-Seiten könnten entstehen?
Empfehlung an Wiki-Kurator: JA / NEIN / BEDINGT – mit Begründung

---

## Status
**Analysiert:** {heute}
**Wiki-Übergabe:** ausstehend

---

Sprache: Deutsch. Ton: präzise, akademisch, lesbar.
Keine Erfindungen – nur was aus den Analysen hervorgeht oder allgemein bekannt ist.

## QUALITÄTS-REFERENZ:
{beispiel}

## WISSENSGRUNDLAGE:
{kontext}"""


# ─────────────────────────────────────────────
#  HILFSFUNKTIONEN
# ─────────────────────────────────────────────

def bibliothek_laden() -> list[dict]:
    with open(BIBLIOTHEK_INDEX, "r", encoding="utf-8") as f:
        return json.load(f).get("buecher", [])


def kontext_laden(buch: dict) -> str:
    """Lädt Index + bestehende Analysen + Quellenliste + Inhaltsanalyse + Bericht."""
    basis = os.path.dirname(buch["lektor_pfad"])
    sekundaer_dir = os.path.join(basis, SEKUNDAER_ORDNER)

    quellen_pfad  = os.path.join(basis, "05_quellen.md")
    analyse_pfad  = os.path.join(basis, "02_inhaltsanalyse.md")
    bericht_pfad  = os.path.join(basis, "04_bericht.md")
    index_pfad    = os.path.join(sekundaer_dir, "06_index.md")

    if not os.path.exists(quellen_pfad):
        return ""

    kontext = f"BUCH: {buch['autor']} – {buch['titel']}\n\n"

    # Prioritäts-Index zuerst – das ist der Startpunkt
    if os.path.exists(index_pfad):
        with open(index_pfad, "r", encoding="utf-8") as f:
            kontext += f"=== PRIORITÄTS-INDEX (06_index.md) ===\n{f.read()}\n\n"

    # Bereits fertige Einzelanalysen
    if os.path.exists(sekundaer_dir):
        for fname in sorted(os.listdir(sekundaer_dir)):
            if fname.startswith("06_") and fname != "06_index.md" and fname.endswith(".md"):
                pfad = os.path.join(sekundaer_dir, fname)
                with open(pfad, "r", encoding="utf-8") as f:
                    kontext += f"=== BEREITS ANALYSIERT: {fname} ===\n{f.read()}\n\n"

    # Rohe Quellenliste
    with open(quellen_pfad, "r", encoding="utf-8") as f:
        kontext += f"=== QUELLENLISTE (05_quellen.md) ===\n{f.read()}\n\n"

    # Inhaltsanalyse und Bericht als Hintergrundwissen
    if os.path.exists(analyse_pfad):
        with open(analyse_pfad, "r", encoding="utf-8") as f:
            kontext += f"=== INHALTSANALYSE ===\n{f.read()}\n\n"

    if os.path.exists(bericht_pfad):
        with open(bericht_pfad, "r", encoding="utf-8") as f:
            kontext += f"=== GESAMTBERICHT ===\n{f.read()}\n\n"

    return kontext


def index_aktualisieren(basis: str, quellen_name: str, dateiname: str) -> None:
    """Setzt den Status einer Quelle im 06_index.md auf ✓ analysiert."""
    index_pfad = os.path.join(basis, SEKUNDAER_ORDNER, "06_index.md")
    if not os.path.exists(index_pfad):
        return

    with open(index_pfad, "r", encoding="utf-8") as f:
        inhalt = f.read()

    # Versuche "→ offen" für diese Quelle auf "✓ analysiert" zu setzen
    # Sucht nach dem Quellennamen in der Zeile und ersetzt den Status
    zeilen = inhalt.splitlines()
    aktualisiert = False
    for i, zeile in enumerate(zeilen):
        if quellen_name.lower() in zeile.lower() and "→ offen" in zeile:
            zeilen[i] = zeile.replace("→ offen", "✓ analysiert")
            aktualisiert = True
            break

    if aktualisiert:
        with open(index_pfad, "w", encoding="utf-8") as f:
            f.write("\n".join(zeilen))
        print(f"  Index aktualisiert: {quellen_name} → ✓ analysiert")


def nach_wiki_kopieren(analyse_pfad: str, wiki_dateiname: str) -> bool:
    """Kopiert eine fertige Analyse nach wiki/raw/ für die Wiki-Injektion."""
    if not os.path.exists(WIKI_RAW_DIR):
        print(f"  Wiki raw/-Ordner nicht gefunden: {WIKI_RAW_DIR}")
        return False

    ziel = os.path.join(WIKI_RAW_DIR, wiki_dateiname)
    shutil.copy2(analyse_pfad, ziel)
    return True


async def _agent_fragen(prompt: str, system_prompt: str) -> str:
    """Sendet einen Prompt an den Agenten, gibt Antwort zurück."""
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".txt", delete=False
    ) as tmp:
        tmp.write(system_prompt)
        tmp_pfad = tmp.name

    options = ClaudeAgentOptions(
        system_prompt=SystemPromptFile(type="file", path=tmp_pfad),
        allowed_tools=[],
        permission_mode="acceptEdits",
        max_turns=2,
    )

    antwort_teile = []
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="", flush=True)
                    antwort_teile.append(block.text)
        elif isinstance(message, ResultMessage):
            if message.is_error:
                print(f"\n[Fehler]: {message.subtype}")

    os.unlink(tmp_pfad)
    return "".join(antwort_teile)


async def einzelanalyse_erstellen(
    gespraech: list[dict],
    kontext: str,
    basis: str,
    buch_autor: str,
    buch_titel: str,
) -> None:
    """Erstellt eine Einzelanalyse pro Quelle – NUR nach doppelter Bestätigung."""

    # Quellennamen vom User abfragen
    print("\n  Welche Quelle soll analysiert werden?")
    print("  Beispiel: 'Reich 1933' oder 'Fanon 1969'")
    try:
        quellen_name = input("  Quelle: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n  Abgebrochen.")
        return

    if not quellen_name:
        print("  Kein Name angegeben – abgebrochen.")
        return

    # Dateiname ableiten: "Reich 1933" → "06_reich_1933.md"
    dateiname = "06_" + re.sub(r"[^a-z0-9]+", "_", quellen_name.lower()).strip("_") + ".md"
    sekundaer_dir = os.path.join(basis, SEKUNDAER_ORDNER)
    ausgabe_pfad = os.path.join(sekundaer_dir, dateiname)

    print(f"\n  Analyse wird gespeichert als: {dateiname}")
    try:
        bestaetigung = input("  Jetzt erstellen? (j/n): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return

    if bestaetigung != "j":
        print("  Abgebrochen – wir diskutieren weiter.\n")
        return

    # Qualitäts-Referenz laden
    beispiel = ""
    if os.path.exists(QUALITAETS_REFERENZ):
        with open(QUALITAETS_REFERENZ, "r", encoding="utf-8") as f:
            beispiel = f.read()

    # Gesprächsverlauf einbauen
    gespraech_text = "\n\nGESPRÄCHSVERLAUF (Honzeles Fokus und Entscheidungen):\n"
    for eintrag in gespraech:
        gespraech_text += f"Honzele: {eintrag['frage']}\n"
        gespraech_text += f"Analyst: {eintrag['antwort'][:800]}\n\n"

    system_prompt = SYSTEM_PROMPT_BERICHT.format(
        kontext=kontext + gespraech_text,
        beispiel=beispiel,
        heute=str(date.today()),
    )

    print(f"\n{'='*60}")
    print(f"  ANALYSE WIRD ERSTELLT: {quellen_name}")
    print(f"{'='*60}\n")

    analyse_prompt = (
        f"Erstelle die Tiefenanalyse für '{quellen_name}' als Sekundärquelle "
        f"von '{buch_titel}' ({buch_autor}). "
        f"Berücksichtige den Gesprächsverlauf und Honzeles Fokus."
    )

    analyse_text = await _agent_fragen(analyse_prompt, system_prompt)

    os.makedirs(sekundaer_dir, exist_ok=True)
    with open(ausgabe_pfad, "w", encoding="utf-8") as f:
        f.write(analyse_text)

    print(f"\n\nGespeichert: {ausgabe_pfad}")
    print(f"  Bitte in der Datei prüfen ob die Analyse vollständig ist.")

    # Index aktualisieren
    index_aktualisieren(basis, quellen_name, dateiname)

    # Wiki-Injektion anbieten
    print(f"\n{'─'*60}")
    print(f"  WIKI-INJEKTION")
    print(f"  Soll diese Analyse nach wiki/raw/ kopiert werden?")
    print(f"  (Danach im Wiki-Projekt injizieren)")
    try:
        wiki_antwort = input("  Ins Wiki? (j/n): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return

    if wiki_antwort == "j":
        # Wiki-Dateiname vorschlagen
        vorschlag = re.sub(r"[^a-zA-Z0-9]+", "_", quellen_name).strip("_")
        vorschlag = f"{vorschlag}_Sekundaeranalyse.md"
        print(f"  Vorgeschlagener Dateiname: {vorschlag}")
        print(f"  Enter = übernehmen, oder eigenen Namen eingeben:")
        try:
            wiki_name = input("  Dateiname: ").strip()
        except (EOFError, KeyboardInterrupt):
            wiki_name = ""
        if not wiki_name:
            wiki_name = vorschlag

        if nach_wiki_kopieren(ausgabe_pfad, wiki_name):
            print(f"\n  Kopiert nach: wiki/raw/{wiki_name}")
            print(f"  Jetzt im Wiki-Projekt öffnen und injizieren:")
            print(f"  → 'Injiziere {wiki_name}'")
        else:
            print("  Kopie fehlgeschlagen – bitte manuell kopieren.")
    else:
        print("  Nicht ins Wiki – Analyse bleibt vorerst lokal.")

    print(f"\n{'='*60}\n")


# ─────────────────────────────────────────────
#  HAUPTFUNKTION
# ─────────────────────────────────────────────

async def sekundaerquellen_analyst_starten() -> None:
    """Startet die interaktive Quellendiskussion."""

    print(f"\n{'='*60}")
    print("  DER SEKUNDÄRQUELLEN-ANALYST")
    print("  Index-gesteuert · Einzelanalysen · Wiki-ready")
    print(f"{'='*60}\n")

    buecher = bibliothek_laden()

    # Nur Bücher mit 05_quellen.md anzeigen
    buecher_mit_quellen = []
    for b in buecher:
        basis = os.path.dirname(b["lektor_pfad"])
        if os.path.exists(os.path.join(basis, "05_quellen.md")):
            buecher_mit_quellen.append(b)

    if not buecher_mit_quellen:
        print("  Kein Buch hat eine 05_quellen.md.")
        print("  Bitte zuerst Quellen extrahieren.")
        return

    print("  Für welches Buch möchtest du Quellen erkunden?\n")
    for i, b in enumerate(buecher_mit_quellen, start=1):
        basis = os.path.dirname(b["lektor_pfad"])
        sekundaer_dir = os.path.join(basis, SEKUNDAER_ORDNER)
        hat_index = os.path.exists(os.path.join(sekundaer_dir, "06_index.md"))
        # Anzahl fertiger Analysen zählen
        anzahl = 0
        if os.path.exists(sekundaer_dir):
            anzahl = len([
                f for f in os.listdir(sekundaer_dir)
                if f.startswith("06_") and f != "06_index.md" and f.endswith(".md")
            ])
        status = f" [Index ✓, {anzahl} Analyse(n)]" if hat_index else (" [kein Index]" if anzahl == 0 else f" [{anzahl} Analyse(n)]")
        print(f"    {i}. {b['autor']}: {b['titel']}{status}")
    print()

    while True:
        try:
            eingabe = input("  Nummer eingeben: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nAuf Wiedersehen, Honzele!")
            return
        if eingabe.isdigit() and 1 <= int(eingabe) <= len(buecher_mit_quellen):
            buch = buecher_mit_quellen[int(eingabe) - 1]
            break
        print(f"  Bitte eine Zahl zwischen 1 und {len(buecher_mit_quellen)} eingeben.")

    print(f"\n  Lade Kontext für: {buch['autor']} – {buch['titel']}...")
    kontext = kontext_laden(buch)

    if not kontext:
        print("  Keine 05_quellen.md gefunden.")
        return

    print(f"  Bereit! ({len(kontext):,} Zeichen geladen)\n")

    basis = os.path.dirname(buch["lektor_pfad"])
    system_prompt_diskussion = SYSTEM_PROMPT_DISKUSSION.format(kontext=kontext)

    print(f"{'='*60}")
    print("  Diskutiere mit dem Quellenanalyst.")
    print("  'B' → Einzelanalyse erstellen")
    print("  'exit' → Beenden")
    print(f"{'='*60}\n")

    # Eröffnung: Agent startet vom Index
    print("Analyst: ", end="", flush=True)
    eroeffnung = await _agent_fragen(
        f"Schaue in den Prioritäts-Index (06_index.md) für '{buch['titel']}' von {buch['autor']}. "
        f"Präsentiere Honzele die 2–3 wichtigsten noch offenen Quellen (★★★★★ zuerst). "
        f"Kurz und konkret mit Stern-Bewertung, dann warte auf seine Reaktion. "
        f"Falls kein Index vorhanden: analysiere die 05_quellen.md und schlage die wichtigsten vor.",
        system_prompt_diskussion
    )
    print("\n")

    gespraech = [{"frage": "[Eröffnung]", "antwort": eroeffnung}]

    while True:
        try:
            eingabe = input("Du: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nAuf Wiedersehen, Honzele!")
            break

        if not eingabe:
            continue

        if eingabe.lower() in ("exit", "quit", "beenden"):
            print("\nAuf Wiedersehen, Honzele!")
            break

        # Analyse-Trigger
        if eingabe.upper() == "B":
            await einzelanalyse_erstellen(
                gespraech, kontext, basis, buch["autor"], buch["titel"]
            )
            # Kontext neu laden – neue Analyse ist jetzt drin
            kontext = kontext_laden(buch)
            system_prompt_diskussion = SYSTEM_PROMPT_DISKUSSION.format(kontext=kontext)
            continue

        # Gesprächskontext aufbauen (letzte 4 Einträge)
        kontext_verlauf = ""
        if gespraech:
            kontext_verlauf = "\n\nBisheriger Gesprächsverlauf:\n"
            for eintrag in gespraech[-4:]:
                kontext_verlauf += f"Honzele: {eintrag['frage']}\n"
                kontext_verlauf += f"Analyst: {eintrag['antwort'][:500]}\n\n"

        prompt = f"{kontext_verlauf}Honzele sagt jetzt: {eingabe}"

        print("\nAnalyst: ", end="", flush=True)
        antwort = await _agent_fragen(prompt, system_prompt_diskussion)
        gespraech.append({"frage": eingabe, "antwort": antwort})
        print("\n")


if __name__ == "__main__":
    asyncio.run(sekundaerquellen_analyst_starten())
