"""
Agent 4: Der Berichterstatter
Liest die vorhandenen Analysen und erstellt das finale Gesamtdossier.
Dies ist das Dokument, das Honzele am Ende in der Hand haelt.
Ergebnis: analysen/<Autor>/<Buch>/04_bericht.md
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import date

from claude_agent_sdk import ClaudeAgentOptions, query
from claude_agent_sdk.types import AssistantMessage, ResultMessage, TextBlock
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()


SYSTEM_PROMPT = """Du bist ein meisterhafter Sachbuch-Rezensent und Wissenskurator.

Du bekommst vorhandene Analysen eines Buches:
1. Die Lektor-Aufbereitung (Inhalt, Struktur, Zitate)
2. Die Inhaltsanalyse (Thesen, Argumentation, Methodik, Einordnung)
3. Optional: die Vernetzungsanalyse (Querverbindungen, Bruecken, weisse Flecken)

Deine Aufgabe: Das finale Gesamtdossier erstellen.

Dies ist KEIN weiterer Analyseschritt - es ist die Destillation.
Du nimmst das Beste aus den vorhandenen Analysen und erschaffst ein einziges,
kohaerentes, lesbares Dokument, das alles enthaelt, was man ueber dieses Buch
wissen muss.

## STRUKTUR DES GESAMTDOSSIERS

### 1. STECKBRIEF
Kompakte Uebersicht: Autor, Titel, Verlag, Jahr, Kernthema, Bewertung in einem Satz.

### 2. DAS BUCH IN 5 SAETZEN
Fuer jemanden, der das Buch nicht kennt: Was ist der Kern? Was ist die Botschaft?
Praezise, klar, ohne Fachjargon.

### 3. KERNTHESEN (Die 3 wichtigsten)
Nicht alle Thesen - nur die 3, die wirklich zaehlen.
Je These: Formulierung plus staerkstes Zitat als Beleg.

### 4. DAS STAERKSTE ARGUMENT DES BUCHES
Was ist die eine Passage, der eine Beweis, das eine Argument, das alles traegt?
Warum ist es so stark?

### 5. DIE WICHTIGSTEN ZITATE
Die 5 Zitate, die man sich merken sollte. Mit Seitenangabe.

### 6. EINORDNUNG UND BEDEUTUNG
Warum ist dieses Buch wichtig? Was leistet es, das andere nicht leisten?
In welchem historischen Moment erschien es?

### 7. VERBINDUNGEN ZUM ARCHIV
Wenn eine Vernetzungsanalyse vorliegt: die 3 wichtigsten Buecher, mit denen man dieses lesen sollte.
Wenn keine Vernetzungsanalyse vorliegt: nur vorsichtige, klar als abgeleitet erkennbare Verbindungen nennen.

### 8. PERSOENLICHE LEKTUEREEMPFEHLUNG
Fuer wen ist dieses Buch? Was nimmt man mit?
Ehrlich, direkt - keine Werbung.

Sprache: Deutsch. Ton: klar, direkt, intellektuell - aber lesbar fuer jeden.
Wenn keine Vernetzungsanalyse vorliegt, erfinde keine Archivbeziehungen."""


async def berichterstatter_erstellen(
    autor: str,
    titel: str,
    lektor_pfad: str,
    inhaltsanalyse_pfad: str,
    vernetzung_pfad: str,
    ausgabe_pfad: str,
) -> None:
    """Erstellt das finale Gesamtdossier aus den vorhandenen Analysen."""

    print(f"\n{'=' * 60}")
    print(f"BERICHTERSTATTER startet: {autor} - {titel}")
    print(f"{'=' * 60}\n")

    print("Vorhandene Analysen werden geladen...")
    with open(lektor_pfad, "r", encoding="utf-8") as handle:
        lektor_text = handle.read()
    with open(inhaltsanalyse_pfad, "r", encoding="utf-8") as handle:
        analyse_text = handle.read()

    vernetzung_text = ""
    hat_vernetzung = os.path.exists(vernetzung_pfad)
    if hat_vernetzung:
        with open(vernetzung_pfad, "r", encoding="utf-8") as handle:
            vernetzung_text = handle.read()

    print(f"  Lektor:          {len(lektor_text):,} Zeichen")
    print(f"  Inhaltsanalyse:  {len(analyse_text):,} Zeichen")
    if hat_vernetzung:
        print(f"  Vernetzung:      {len(vernetzung_text):,} Zeichen\n")
    else:
        print("  Vernetzung:      fehlt - Bericht nutzt nur 01+02\n")

    vernetzung_block = (
        vernetzung_text[:8000]
        if vernetzung_text
        else "Keine Vernetzungsanalyse vorhanden. Wenn noetig, leite Verbindungen nur vorsichtig aus den vorhandenen Analysen ab und erfinde keine Archivbeziehungen."
    )

    prompt = f"""Hier sind die vorhandenen Analysen des Buches "{titel}" von {autor}.

--- LEKTOR-AUFBEREITUNG ---
{lektor_text[:12000]}

--- INHALTSANALYSE ---
{analyse_text[:12000]}

--- VERNETZUNGSANALYSE ---
{vernetzung_block}

Bitte erstelle nun das finale Gesamtdossier.
Destilliere das Wesentliche - praezise, klar, unvergesslich."""

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=[],
        permission_mode="acceptEdits",
        max_turns=3,
    )

    print("Berichterstatter schreibt das Dossier...\n")
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
                print(f"\n\n[Kosten: ${kosten:.4f} | Durchlaeufe: {message.num_turns}]")

    print("\n" + "-" * 60)

    ergebnis = "".join(ergebnis_teile)
    os.makedirs(os.path.dirname(ausgabe_pfad), exist_ok=True)
    with open(ausgabe_pfad, "w", encoding="utf-8") as handle:
        handle.write(f"# GESAMTDOSSIER: {titel}\n")
        handle.write(f"### {autor}\n\n")
        handle.write(f"**Erstellt am:** {date.today()}  \n")
        grundlage = "Lektor + Inhaltsanalyse"
        if hat_vernetzung:
            grundlage += " + Vernetzung"
        handle.write(f"**Grundlage:** {grundlage}  \n\n")
        handle.write("---\n\n")
        handle.write(ergebnis)

    print(f"\nGespeichert: {ausgabe_pfad}")
    print(f"\n{'=' * 60}")
    print(f"ANALYSE VOLLSTAENDIG - {titel}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    asyncio.run(
        berichterstatter_erstellen(
            autor="Michael Lueders",
            titel="Krieg ohne Ende",
            lektor_pfad=r"E:\Claude_Projekte\Buchanalysen\analysen\Michael_Luders\Krieg_ohne_Ende\01_lektor.md",
            inhaltsanalyse_pfad=r"E:\Claude_Projekte\Buchanalysen\analysen\Michael_Luders\Krieg_ohne_Ende\02_inhaltsanalyse.md",
            vernetzung_pfad=r"E:\Claude_Projekte\Buchanalysen\analysen\Michael_Luders\Krieg_ohne_Ende\03_vernetzung.md",
            ausgabe_pfad=r"E:\Claude_Projekte\Buchanalysen\analysen\Michael_Luders\Krieg_ohne_Ende\04_bericht.md",
        )
    )
