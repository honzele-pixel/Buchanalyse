"""
Agent 4: Der Berichterstatter
Liest alle drei vorherigen Analysen und erstellt das finale Gesamtdossier.
Dies ist das Dokument das Honzele am Ende in der Hand hält.
Ergebnis: analysen/<Autor>/<Buch>/04_bericht.md
"""

import asyncio
import os
import sys
from datetime import date
from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import AssistantMessage, TextBlock, ResultMessage

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()


SYSTEM_PROMPT = """Du bist ein meisterhafter Sachbuch-Rezensent und Wissenskurator.

Du bekommst drei Analysen eines Buches:
1. Die Lektor-Aufbereitung (Inhalt, Struktur, Zitate)
2. Die Inhaltsanalyse (Thesen, Argumentation, Methodik, Einordnung)
3. Die Vernetzungsanalyse (Querverbindungen, Brücken, weiße Flecken)

Deine Aufgabe: Das finale Gesamtdossier erstellen.

Dies ist KEIN weiterer Analyseschritt – es ist die Destillation.
Du nimmst das Beste aus allen drei Analysen und erschaffst ein einziges,
kohärentes, lesbares Dokument das alles enthält was man über dieses Buch
wissen muss.

---

## STRUKTUR DES GESAMTDOSSIERS
(Kein Bezug zur Website "Archiv der Souveränität" – das ist ein separates Projekt!)

### 1. STECKBRIEF
Kompakte Übersicht: Autor, Titel, Verlag, Jahr, Kernthema, Bewertung in einem Satz.

### 2. DAS BUCH IN 5 SÄTZEN
Für jemanden der das Buch nicht kennt: Was ist der Kern? Was ist die Botschaft?
Präzise, klar, ohne Fachjargon.

### 3. KERNTHESEN (Die 3 wichtigsten)
Nicht alle Thesen – nur die 3 die wirklich zählen.
Je These: Formulierung + stärkstes Zitat als Beleg.

### 4. DAS STÄRKSTE ARGUMENT DES BUCHES
Was ist die eine Passage, der eine Beweis, das eine Argument das alles trägt?
Warum ist es so stark?

### 5. DIE WICHTIGSTEN ZITATE
Die 5 Zitate die man sich merken sollte. Mit Seitenangabe.

### 6. EINORDNUNG & BEDEUTUNG
Warum ist dieses Buch wichtig? Was leistet es das andere nicht leisten?
In welchem historischen Moment erschien es?

### 7. VERBINDUNGEN ZUM ARCHIV
Die 3 wichtigsten Bücher mit denen man dieses lesen sollte.
Je eines: Titel + ein Satz warum.

### 8. PERSÖNLICHE LEKTÜREEMPFEHLUNG
Für wen ist dieses Buch? Was nimmt man mit?
Ehrlich, direkt – keine Werbung.

---

Sprache: Deutsch. Ton: klar, direkt, intellektuell – aber lesbar für jeden.
Dies ist das Dokument das bleibt. Mach es gut."""


async def berichterstatter_erstellen(
    autor: str,
    titel: str,
    lektor_pfad: str,
    inhaltsanalyse_pfad: str,
    vernetzung_pfad: str,
    ausgabe_pfad: str
) -> None:
    """Erstellt das finale Gesamtdossier aus allen drei Analysen."""

    print(f"\n{'='*60}")
    print(f"BERICHTERSTATTER startet: {autor} – {titel}")
    print(f"{'='*60}\n")

    # Alle drei Analysen laden
    print("Alle Analysen werden geladen...")
    with open(lektor_pfad, "r", encoding="utf-8") as f:
        lektor_text = f.read()
    with open(inhaltsanalyse_pfad, "r", encoding="utf-8") as f:
        analyse_text = f.read()
    with open(vernetzung_pfad, "r", encoding="utf-8") as f:
        vernetzung_text = f.read()

    print(f"  Lektor:          {len(lektor_text):,} Zeichen")
    print(f"  Inhaltsanalyse:  {len(analyse_text):,} Zeichen")
    print(f"  Vernetzung:      {len(vernetzung_text):,} Zeichen\n")

    prompt = f"""Hier sind alle drei Analysen des Buches "{titel}" von {autor}.

--- LEKTOR-AUFBEREITUNG ---
{lektor_text[:12000]}

--- INHALTSANALYSE ---
{analyse_text[:12000]}

--- VERNETZUNGSANALYSE ---
{vernetzung_text[:8000]}

Bitte erstelle nun das finale Gesamtdossier.
Destilliere das Wesentliche – präzise, klar, unvergesslich."""

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
                print(f"\n\n[Kosten: ${kosten:.4f} | Durchläufe: {message.num_turns}]")

    print("\n" + "-" * 60)

    # Finales Dossier speichern
    ergebnis = "".join(ergebnis_teile)
    os.makedirs(os.path.dirname(ausgabe_pfad), exist_ok=True)
    with open(ausgabe_pfad, "w", encoding="utf-8") as f:
        f.write(f"# GESAMTDOSSIER: {titel}\n")
        f.write(f"### {autor}\n\n")
        f.write(f"**Erstellt am:** {date.today()}  \n")
        f.write(f"**Grundlage:** Lektor + Inhaltsanalyse + Vernetzung  \n\n")
        f.write("---\n\n")
        f.write(ergebnis)

    print(f"\nGespeichert: {ausgabe_pfad}")
    print(f"\n{'='*60}")
    print(f"ANALYSE VOLLSTÄNDIG – {titel}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(berichterstatter_erstellen(
        autor               = "Michael Lüders",
        titel               = "Krieg ohne Ende",
        lektor_pfad         = r"E:\Claude_Projekte\Buchanalysen\analysen\Michael_Luders\Krieg_ohne_Ende\01_lektor.md",
        inhaltsanalyse_pfad = r"E:\Claude_Projekte\Buchanalysen\analysen\Michael_Luders\Krieg_ohne_Ende\02_inhaltsanalyse.md",
        vernetzung_pfad     = r"E:\Claude_Projekte\Buchanalysen\analysen\Michael_Luders\Krieg_ohne_Ende\03_vernetzung.md",
        ausgabe_pfad        = r"E:\Claude_Projekte\Buchanalysen\analysen\Michael_Luders\Krieg_ohne_Ende\04_bericht.md",
    ))
