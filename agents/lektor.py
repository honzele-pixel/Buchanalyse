"""
Agent 1: Der Lektor
Liest ein PDF vollstaendig aus und bereitet den Text strukturiert auf.
Das Buch wird in Abschnitte aufgeteilt und Schritt fuer Schritt verarbeitet.
Ergebnis: analysen/<Autor>/<Buch>/01_lektor.md

Kostenstrategie:
- primaer lokal ueber Ollama
- Cloud nur als Fallback fuer den Lektor
"""

from __future__ import annotations

import asyncio
import os
import shutil
import sys

import anthropic
import fitz  # PyMuPDF
from claude_agent_sdk import ClaudeAgentOptions, query
from claude_agent_sdk.types import AssistantMessage, ResultMessage, TextBlock
from dotenv import load_dotenv

from config import settings
from pipeline.local_llm import LocalLLMError, ollama_generieren, ollama_verfuegbar

# Windows-Konsole auf UTF-8 stellen
sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

# Wie viele Zeichen pro Abschnitt (ca. 60 Seiten)
ZEICHEN_PRO_ABSCHNITT = 80_000


SYSTEM_PROMPT_ABSCHNITT = """Du bist ein praeziser Lektor und Textaufbereiter.

Du bekommst einen Abschnitt eines Buches (mit Seitenangaben).
Deine Aufgabe:

1. Kapitel und Abschnitte: Erkenne welche Kapitel und Abschnitte in diesem Teil vorkommen
2. Kerninhalt: Fasse jeden Abschnitt in 3-5 praegnanten Saetzen zusammen
3. Wichtige Zitate: Markiere woertliche Zitate mit Seitenangabe (Format: > "Zitat" - S. XX)
4. Schluesselbegriffe: Liste neue wichtige Begriffe und Konzepte in diesem Abschnitt

Ausgabe: Strukturiertes Markdown. Sprache: Deutsch.
Sei vollstaendig - dieser Text ist die Grundlage fuer alle weiteren Analysen."""


SYSTEM_PROMPT_SYNTHESE = """Du bist ein erfahrener Literaturanalyst.

Du bekommst die aufbereiteten Zusammenfassungen aller Buchteile eines Werkes.
Deine Aufgabe: Erstelle daraus ein einheitliches, strukturiertes Gesamtdokument mit:

1. Bibliografische Daten - Titel, Autor, Verlag, Jahr
2. Gesamtstruktur - Alle Kapitel in der richtigen Reihenfolge
3. Kapitelzusammenfassungen - Kerninhalt je Kapitel (aus den Einzelteilen zusammengefuehrt)
4. Wichtigste Zitate - Die 10-15 aussagekraeftigsten Zitate aus dem ganzen Buch
5. Schluesselbegriffe - Vollstaendige Liste aller wichtigen Begriffe und Konzepte
6. Schluesselpersonen - Alle erwaehnten wichtigen Personen mit kurzer Beschreibung

Ausgabe: Sauberes, einheitliches Markdown. Sprache: Deutsch."""


def pdf_lesen(pdf_pfad: str) -> tuple[str, int]:
    """Liest ein PDF und gibt den Rohtext plus Seitenzahl zurueck."""
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
    """Teilt den Text in gleichmaessige Abschnitte auf - an Seitengrenzen."""
    teile = []
    start = 0

    while start < len(text):
        ende = start + zeichen_pro_teil

        if ende >= len(text):
            teile.append(text[start:])
            break

        naechste_seite = text.find("\n\n[Seite ", ende)
        if naechste_seite != -1 and naechste_seite < ende + 5000:
            ende = naechste_seite

        teile.append(text[start:ende])
        start = ende

    return teile


def lokaler_lektor_aktiv() -> bool:
    """Prueft, ob der Standardprovider lokal genutzt werden soll."""
    return settings.LEKTOR_PROVIDER == "ollama" and ollama_verfuegbar()


def lokaler_abschnitt_prompt(abschnitt: str, teil_nr: int, gesamt: int) -> str:
    return f"""Hier ist Abschnitt {teil_nr} von {gesamt} des Buches.

--- ABSCHNITT ANFANG ---
{abschnitt}
--- ABSCHNITT ENDE ---

Bitte aufbereiten gemaess deinen Anweisungen."""


def lokaler_synthese_prompt(alle_teile: list[str], buch_titel: str) -> str:
    teile_text = "\n\n---NEUER ABSCHNITT---\n\n".join(
        [f"## Teil {i + 1}\n{t}" for i, t in enumerate(alle_teile)]
    )
    return (
        f'Hier sind alle {len(alle_teile)} aufbereiteten Abschnitte des Buches "{buch_titel}":\n\n'
        f"{teile_text}\n\n"
        "Bitte erstelle daraus ein einheitliches Gesamtdokument."
    )


def lokale_abschnitt_analyse(abschnitt: str, teil_nr: int, gesamt: int) -> str:
    """Lokale Abschnittsanalyse ueber Ollama."""
    return ollama_generieren(
        prompt=lokaler_abschnitt_prompt(abschnitt, teil_nr, gesamt),
        system_prompt=SYSTEM_PROMPT_ABSCHNITT,
    )


def lokale_synthese(alle_teile: list[str], buch_titel: str) -> str:
    """Lokale Synthese ueber Ollama."""
    return ollama_generieren(
        prompt=lokaler_synthese_prompt(alle_teile, buch_titel),
        system_prompt=SYSTEM_PROMPT_SYNTHESE,
    )


async def cloud_abschnitt_analysieren(abschnitt: str, teil_nr: int, gesamt: int) -> str:
    """Cloud-Fallback fuer einen Textabschnitt."""
    prompt = lokaler_abschnitt_prompt(abschnitt, teil_nr, gesamt)

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
    print(f"  Abschnitt {teil_nr}/{gesamt} fertig (${kosten:.4f}, Cloud-Fallback)")
    return ergebnis


def cloud_synthese_erstellen(alle_teile: list[str], buch_titel: str) -> str:
    """Cloud-Fallback fuer die Gesamtsynthese (direkte Anthropic-API)."""
    client = anthropic.Anthropic()
    ergebnis_teile = []

    with client.messages.stream(
        model=settings.LEKTOR_FALLBACK_MODEL,
        max_tokens=8192,
        system=SYSTEM_PROMPT_SYNTHESE,
        messages=[
            {
                "role": "user",
                "content": lokaler_synthese_prompt(alle_teile, buch_titel),
            }
        ],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            ergebnis_teile.append(text)

    print()
    return "".join(ergebnis_teile)


async def abschnitt_analysieren(abschnitt: str, teil_nr: int, gesamt: int) -> str:
    """Fuehrt eine Abschnittsanalyse lokal aus, mit Cloud-Fallback."""
    if lokaler_lektor_aktiv():
        try:
            ergebnis = lokale_abschnitt_analyse(abschnitt, teil_nr, gesamt)
            print(f"  Abschnitt {teil_nr}/{gesamt} fertig (lokal)")
            return ergebnis
        except LocalLLMError as exc:
            print(f"  [Warnung] Lokaler Lektor fuer Abschnitt {teil_nr} fehlgeschlagen: {exc}")

    return await cloud_abschnitt_analysieren(abschnitt, teil_nr, gesamt)


def synthese_erstellen(alle_teile: list[str], buch_titel: str) -> str:
    """Fuehrt die Buchsynthese lokal aus, mit Cloud-Fallback."""
    if lokaler_lektor_aktiv():
        try:
            print("  Synthese laeuft lokal ueber Ollama...")
            return lokale_synthese(alle_teile, buch_titel)
        except LocalLLMError as exc:
            print(f"  [Warnung] Lokale Synthese fehlgeschlagen: {exc}")

    print("  Synthese faellt auf Anthropic zurueck...")
    return cloud_synthese_erstellen(alle_teile, buch_titel)


async def lektor_analysieren(pdf_pfad: str, ausgabe_pfad: str) -> None:
    """Liest das gesamte PDF und laesst es vollstaendig aufbereiten."""

    buch_name = os.path.splitext(os.path.basename(pdf_pfad))[0]
    print(f"\n{'=' * 60}")
    print(f"LEKTOR startet: {buch_name}")
    print(f"{'=' * 60}\n")

    if lokaler_lektor_aktiv():
        print(f"Provider: lokal ({settings.LEKTOR_PROVIDER}:{settings.LEKTOR_MODEL})")
    else:
        print(
            "Provider: Cloud-Fallback "
            f"({settings.LEKTOR_FALLBACK_PROVIDER}:{settings.LEKTOR_FALLBACK_MODEL})"
        )

    print("Schritt 1: PDF wird gelesen...")
    rohtext, seitenanzahl = pdf_lesen(pdf_pfad)
    print(f"  {seitenanzahl} Seiten | {len(rohtext):,} Zeichen gesamt\n")

    abschnitte = text_aufteilen(rohtext, ZEICHEN_PRO_ABSCHNITT)
    print(f"Schritt 2: Text in {len(abschnitte)} Abschnitte aufgeteilt")
    for i, abschnitt in enumerate(abschnitte, start=1):
        print(f"  Abschnitt {i}: {len(abschnitt):,} Zeichen")
    print()

    cache_dir = os.path.join(os.path.dirname(ausgabe_pfad), ".chunk_cache")
    os.makedirs(cache_dir, exist_ok=True)

    print(f"Schritt 3: Analyse der {len(abschnitte)} Abschnitte...")
    abschnitt_analysen = []

    for i, abschnitt in enumerate(abschnitte, start=1):
        cache_pfad = os.path.join(cache_dir, f"chunk_{i:02d}.md")

        if os.path.exists(cache_pfad):
            print(f"  Abschnitt {i}/{len(abschnitte)} - aus Cache geladen")
            with open(cache_pfad, "r", encoding="utf-8") as handle:
                abschnitt_analysen.append(handle.read())
            continue

        analyse = await abschnitt_analysieren(abschnitt, i, len(abschnitte))
        abschnitt_analysen.append(analyse)
        with open(cache_pfad, "w", encoding="utf-8") as handle:
            handle.write(analyse)

    print()

    print("Schritt 4: Synthese - Gesamtdokument wird erstellt...")
    print("-" * 60)
    finale_analyse = synthese_erstellen(abschnitt_analysen, buch_name)
    print("-" * 60)

    os.makedirs(os.path.dirname(ausgabe_pfad), exist_ok=True)
    with open(ausgabe_pfad, "w", encoding="utf-8") as handle:
        handle.write(f"# Lektor-Aufbereitung: {buch_name}\n\n")
        handle.write(f"**Quelle:** {pdf_pfad}  \n")
        handle.write(f"**Seiten:** {seitenanzahl}  \n")
        handle.write(f"**Abschnitte verarbeitet:** {len(abschnitte)}  \n\n")
        handle.write("---\n\n")
        handle.write(finale_analyse)

    shutil.rmtree(cache_dir, ignore_errors=True)

    print(f"\nGespeichert: {ausgabe_pfad}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    PDF_PFAD = r"E:\Bucher\Michael_Luders\Krieg_ohne_Ende.pdf"
    AUSGABE = r"E:\Claude_Projekte\Buchanalysen\analysen\Michael_Luders\Krieg_ohne_Ende\01_lektor.md"
    asyncio.run(lektor_analysieren(PDF_PFAD, AUSGABE))
