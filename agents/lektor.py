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

import fitz  # PyMuPDF
from bs4 import BeautifulSoup
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


def epub_lesen(epub_pfad: str) -> tuple[str, int]:
    """Liest ein EPUB und gibt den Rohtext plus Kapitelanzahl zurueck."""
    import zipfile
    import re

    text_teile = []
    kapitel_nr = 0

    with zipfile.ZipFile(epub_pfad, "r") as zf:
        html_dateien = sorted(
            [n for n in zf.namelist() if re.search(r"\.(html|xhtml|htm)$", n, re.I)]
        )
        for dateiname in html_dateien:
            try:
                inhalt = zf.read(dateiname).decode("utf-8", errors="replace")
            except Exception:
                continue
            soup = BeautifulSoup(inhalt, "html.parser")
            text = soup.get_text(separator="\n").strip()
            if len(text) > 100:
                kapitel_nr += 1
                text_teile.append(f"[Kapitel {kapitel_nr}]\n{text}")

    return "\n\n".join(text_teile), kapitel_nr


def text_aufteilen(text: str, zeichen_pro_teil: int) -> list[str]:
    """Teilt den Text in gleichmaessige Abschnitte auf - an Seiten- oder Kapitelgrenzen."""
    teile = []
    start = 0

    while start < len(text):
        ende = start + zeichen_pro_teil

        if ende >= len(text):
            teile.append(text[start:])
            break

        naechste_grenze = -1
        for marker in ("\n\n[Seite ", "\n\n[Kapitel "):
            pos = text.find(marker, ende)
            if pos != -1 and pos < ende + 5000:
                if naechste_grenze == -1 or pos < naechste_grenze:
                    naechste_grenze = pos

        if naechste_grenze != -1:
            ende = naechste_grenze

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


async def abschnitt_analysieren(abschnitt: str, teil_nr: int, gesamt: int) -> str:
    """Fuehrt eine Abschnittsanalyse lokal ueber Ollama aus."""
    if not lokaler_lektor_aktiv():
        raise SystemExit(
            "\n  [FEHLER] Ollama nicht erreichbar oder LEKTOR_PROVIDER != 'ollama'.\n"
            "  Bitte Ollama starten und Modell pruefen (settings.py: LEKTOR_MODEL).\n"
            "  Kein Cloud-Fallback – der Lektor laeuft ausschliesslich lokal."
        )
    ergebnis = lokale_abschnitt_analyse(abschnitt, teil_nr, gesamt)
    print(f"  Abschnitt {teil_nr}/{gesamt} fertig (lokal)")
    return ergebnis


def synthese_erstellen(alle_teile: list[str], buch_titel: str) -> str:
    """Fuehrt die Buchsynthese lokal ueber Ollama aus."""
    if not lokaler_lektor_aktiv():
        raise SystemExit(
            "\n  [FEHLER] Ollama nicht erreichbar fuer Synthese.\n"
            "  Kein Cloud-Fallback – der Lektor laeuft ausschliesslich lokal."
        )
    print("  Synthese laeuft lokal ueber Ollama...")
    return lokale_synthese(alle_teile, buch_titel)


async def lektor_analysieren(pdf_pfad: str, ausgabe_pfad: str) -> None:
    """Liest das gesamte PDF oder EPUB und laesst es vollstaendig aufbereiten."""

    buch_name = os.path.splitext(os.path.basename(pdf_pfad))[0]
    ist_epub = pdf_pfad.lower().endswith(".epub")

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

    if ist_epub:
        print("Schritt 1: EPUB wird gelesen...")
        rohtext, seitenanzahl = epub_lesen(pdf_pfad)
        einheit = "Kapitel"
    else:
        print("Schritt 1: PDF wird gelesen...")
        rohtext, seitenanzahl = pdf_lesen(pdf_pfad)
        einheit = "Seiten"
    print(f"  {seitenanzahl} {einheit} | {len(rohtext):,} Zeichen gesamt\n")

    abschnitte = text_aufteilen(rohtext, ZEICHEN_PRO_ABSCHNITT)
    print(f"Schritt 2: Text in {len(abschnitte)} Abschnitte aufgeteilt")
    for i, abschnitt in enumerate(abschnitte, start=1):
        print(f"  Abschnitt {i}: {len(abschnitt):,} Zeichen")
    print()

    # Neu: Rohtext-Chunks speichern (extrem wertvoll!)
    rohtext_dir = os.path.join(os.path.dirname(ausgabe_pfad), "01_lektor_rohtext")
    os.makedirs(rohtext_dir, exist_ok=True)
    for i, abschnitt in enumerate(abschnitte, start=1):
        rohtext_pfad = os.path.join(rohtext_dir, f"raw_chunk_{i:02d}.txt")
        with open(rohtext_pfad, "w", encoding="utf-8") as handle:
            handle.write(abschnitt)
    print(f"  Alle {len(abschnitte)} Rohtext-Chunks gespeichert in: {rohtext_dir}")

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
        handle.write(f"**{einheit.capitalize()}:** {seitenanzahl}  \n")
        handle.write(f"**Abschnitte verarbeitet:** {len(abschnitte)}  \n\n")
        handle.write("---\n\n")
        handle.write(finale_analyse)

    # Cache nicht loeschen, sondern als Detail-Ebene behalten
    details_dir = os.path.join(os.path.dirname(ausgabe_pfad), "01_lektor_details")
    if os.path.exists(details_dir):
        shutil.rmtree(details_dir)
    os.rename(cache_dir, details_dir)

    print(f"\nGespeichert: {ausgabe_pfad}")
    print(f"Details gespeichert in: {details_dir}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    PDF_PFAD = r"E:\Bucher\Michael_Luders\Krieg_ohne_Ende.pdf"
    AUSGABE = r"E:\Claude_Projekte\Buchanalysen\analysen\Michael_Luders\Krieg_ohne_Ende\01_lektor.md"
    asyncio.run(lektor_analysieren(PDF_PFAD, AUSGABE))
