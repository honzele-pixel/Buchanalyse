"""
Agent 1: Der Lektor
Liest ein PDF vollständig aus und bereitet den Text strukturiert auf.
Das Buch wird in Abschnitte aufgeteilt und Schritt für Schritt verarbeitet.
Ergebnis: analysen/<Autor>/<Buch>/01_lektor.md
"""

import asyncio
import os
import sys
import tempfile
import fitz  # PyMuPDF
from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import AssistantMessage, TextBlock, ResultMessage, SystemPromptFile

# Windows-Konsole auf UTF-8 stellen
sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

# Wie viele Zeichen pro Abschnitt (ca. 60 Seiten)
ZEICHEN_PRO_ABSCHNITT = 80_000


SYSTEM_PROMPT_ABSCHNITT = """Du bist ein präziser Lektor und Textaufbereiter.

Du bekommst einen Abschnitt eines Buches (mit Seitenangaben).
Deine Aufgabe:

1. **Kapitel & Abschnitte** – Erkenne welche Kapitel/Abschnitte in diesem Teil vorkommen
2. **Kerninhalt** – Fasse jeden Abschnitt in 3-5 prägnanten Sätzen zusammen
3. **Wichtige Zitate** – Markiere wörtliche Zitate mit Seitenangabe (Format: > "Zitat" — S. XX)
4. **Schlüsselbegriffe** – Liste neue wichtige Begriffe und Konzepte in diesem Abschnitt

Ausgabe: Strukturiertes Markdown. Sprache: Deutsch.
Sei vollständig – dieser Text ist die Grundlage für alle weiteren Analysen."""


SYSTEM_PROMPT_SYNTHESE = """Du bist ein erfahrener Literaturanalyst.

Du bekommst die aufbereiteten Zusammenfassungen aller Buchteile eines Werkes.
Deine Aufgabe: Erstelle daraus ein einheitliches, strukturiertes Gesamtdokument mit:

1. **Bibliografische Daten** – Titel, Autor, Verlag, Jahr
2. **Gesamtstruktur** – Alle Kapitel in der richtigen Reihenfolge
3. **Kapitelzusammenfassungen** – Kerninhalt je Kapitel (aus den Einzelteilen zusammengeführt)
4. **Wichtigste Zitate** – Die 10-15 aussagekräftigsten Zitate aus dem ganzen Buch
5. **Schlüsselbegriffe** – Vollständige Liste aller wichtigen Begriffe und Konzepte
6. **Schlüsselpersonen** – Alle erwähnten wichtigen Personen mit kurzer Beschreibung

Ausgabe: Sauberes, einheitliches Markdown. Sprache: Deutsch."""


def pdf_lesen(pdf_pfad: str) -> tuple[str, int]:
    """Liest ein PDF und gibt den Rohtext + Seitenzahl zurück."""
    doc = fitz.open(pdf_pfad)
    seitenanzahl = len(doc)
    text_teile = []

    for seite_nr, seite in enumerate(doc, start=1):
        text = seite.get_text()
        if text.strip():
            text_teile.append(f"[Seite {seite_nr}]\n{text}")

    doc.close()
    return "\n\n".join(text_teile), seitenanzahl


def text_aufteilen(text: str, zeichen_pro_teil: int) -> list[str]:
    """Teilt den Text in gleichmäßige Abschnitte auf – an Seitengrenzen."""
    teile = []
    start = 0

    while start < len(text):
        ende = start + zeichen_pro_teil

        if ende >= len(text):
            teile.append(text[start:])
            break

        # An einer Seitengrenze [Seite X] schneiden
        naechste_seite = text.find("\n\n[Seite ", ende)
        if naechste_seite != -1 and naechste_seite < ende + 5000:
            ende = naechste_seite

        teile.append(text[start:ende])
        start = ende

    return teile


async def abschnitt_analysieren(abschnitt: str, teil_nr: int, gesamt: int) -> str:
    """Lässt Claude einen Textabschnitt aufbereiten."""
    prompt = f"""Hier ist Abschnitt {teil_nr} von {gesamt} des Buches.

--- ABSCHNITT ANFANG ---
{abschnitt}
--- ABSCHNITT ENDE ---

Bitte aufbereiten gemäß deinen Anweisungen."""

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT_ABSCHNITT,
        allowed_tools=[],
        permission_mode="acceptEdits",
        max_turns=2,
    )

    ergebnis_teile = []
    kosten = 0.0

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    ergebnis_teile.append(block.text)
        elif isinstance(message, ResultMessage):
            if message.is_error:
                print(f"  [Fehler bei Abschnitt {teil_nr}]")
            elif message.total_cost_usd is not None:
                kosten = message.total_cost_usd

    ergebnis = "".join(ergebnis_teile)
    print(f"  Abschnitt {teil_nr}/{gesamt} fertig (${kosten:.4f})")
    return ergebnis


async def synthese_erstellen(alle_teile: list[str], buch_titel: str) -> str:
    """Fasst alle Abschnitt-Analysen zu einem Gesamtdokument zusammen."""
    teile_text = "\n\n---NEUER ABSCHNITT---\n\n".join(
        [f"## Teil {i+1}\n{t}" for i, t in enumerate(alle_teile)]
    )

    # Vollständiger System-Prompt mit allen Chunk-Analysen als Datei (Windows-Limit umgehen)
    system_prompt_inhalt = f"""{SYSTEM_PROMPT_SYNTHESE}

## AUFBEREITETE ABSCHNITTE DES BUCHES "{buch_titel}":

{teile_text}"""

    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".txt", delete=False
    ) as tmp:
        tmp.write(system_prompt_inhalt)
        tmp_pfad = tmp.name

    options = ClaudeAgentOptions(
        system_prompt=SystemPromptFile(type="file", path=tmp_pfad),
        allowed_tools=[],
        permission_mode="acceptEdits",
        max_turns=1,
    )

    ergebnis_teile = []
    kosten = 0.0

    async for message in query(
        prompt=f'Erstelle das einheitliche Gesamtdokument für "{buch_titel}".',
        options=options
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="", flush=True)
                    ergebnis_teile.append(block.text)
        elif isinstance(message, ResultMessage):
            if message.is_error:
                print(f"\n[Fehler bei Synthese]")
            elif message.total_cost_usd is not None:
                kosten = message.total_cost_usd
                print(f"\n\n[Synthese-Kosten: ${kosten:.4f}]")

    os.unlink(tmp_pfad)
    return "".join(ergebnis_teile)


async def lektor_analysieren(pdf_pfad: str, ausgabe_pfad: str) -> None:
    """Liest das gesamte PDF und lässt Claude es vollständig aufbereiten."""

    buch_name = os.path.splitext(os.path.basename(pdf_pfad))[0]
    print(f"\n{'='*60}")
    print(f"LEKTOR startet: {buch_name}")
    print(f"{'='*60}\n")

    # 1. PDF lesen
    print("Schritt 1: PDF wird gelesen...")
    rohtext, seitenanzahl = pdf_lesen(pdf_pfad)
    print(f"  {seitenanzahl} Seiten | {len(rohtext):,} Zeichen gesamt\n")

    # 2. In Abschnitte aufteilen
    abschnitte = text_aufteilen(rohtext, ZEICHEN_PRO_ABSCHNITT)
    print(f"Schritt 2: Text in {len(abschnitte)} Abschnitte aufgeteilt")
    for i, a in enumerate(abschnitte):
        print(f"  Abschnitt {i+1}: {len(a):,} Zeichen")
    print()

    # 3. Jeden Abschnitt einzeln analysieren (mit Zwischenspeicherung)
    cache_dir = os.path.join(os.path.dirname(ausgabe_pfad), ".chunk_cache")
    os.makedirs(cache_dir, exist_ok=True)

    print(f"Schritt 3: Analyse der {len(abschnitte)} Abschnitte...")
    abschnitt_analysen = []

    for i, abschnitt in enumerate(abschnitte):
        cache_pfad = os.path.join(cache_dir, f"chunk_{i+1:02d}.md")

        if os.path.exists(cache_pfad):
            print(f"  Abschnitt {i+1}/{len(abschnitte)} – aus Cache geladen")
            with open(cache_pfad, "r", encoding="utf-8") as f:
                abschnitt_analysen.append(f.read())
        else:
            analyse = await abschnitt_analysieren(abschnitt, i + 1, len(abschnitte))
            abschnitt_analysen.append(analyse)
            with open(cache_pfad, "w", encoding="utf-8") as f:
                f.write(analyse)

    print()

    # 4. Synthese – alles zusammenführen
    print("Schritt 4: Synthese – Gesamtdokument wird erstellt...")
    print("-" * 60)
    finale_analyse = await synthese_erstellen(abschnitt_analysen, buch_name)
    print("-" * 60)

    # 5. Speichern + Cache löschen
    os.makedirs(os.path.dirname(ausgabe_pfad), exist_ok=True)
    with open(ausgabe_pfad, "w", encoding="utf-8") as f:
        f.write(f"# Lektor-Aufbereitung: {buch_name}\n\n")
        f.write(f"**Quelle:** {pdf_pfad}  \n")
        f.write(f"**Seiten:** {seitenanzahl}  \n")
        f.write(f"**Abschnitte verarbeitet:** {len(abschnitte)}  \n\n")
        f.write("---\n\n")
        f.write(finale_analyse)

    # Cache aufräumen
    import shutil
    shutil.rmtree(cache_dir, ignore_errors=True)

    print(f"\nGespeichert: {ausgabe_pfad}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    PDF_PFAD = r"E:\Bucher\Michael_Luders\Krieg_ohne_Ende.pdf"
    AUSGABE  = r"E:\Claude_Projekte\Buchanalysen\analysen\Michael_Luders\Krieg_ohne_Ende\01_lektor.md"
    asyncio.run(lektor_analysieren(PDF_PFAD, AUSGABE))
