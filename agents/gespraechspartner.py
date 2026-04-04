"""
Agent 5: Der Gesprächspartner
Ermöglicht Honzele eine echte Diskussion über die analysierten Bücher.
Stützt sich AUSSCHLIESSLICH auf die vorhandenen Analysen – keine Halluzinationen.

Verwendung: wird von main.py aufgerufen
"""

import asyncio
import os
import sys
import json
import tempfile
from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import AssistantMessage, TextBlock, ResultMessage, UserMessage, SystemPromptFile

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

BIBLIOTHEK_INDEX  = r"E:\Claude_Projekte\Buchanalysen\bibliothek\index.json"
ANALYSEN_DIR      = r"E:\Claude_Projekte\Buchanalysen\analysen"


def bibliothek_laden() -> list[dict]:
    """Lädt die Buchliste aus dem Index."""
    with open(BIBLIOTHEK_INDEX, "r", encoding="utf-8") as f:
        bibliothek = json.load(f)
    return bibliothek.get("buecher", [])


def buch_laden(buch: dict) -> str:
    """Lädt die Analysen eines einzelnen Buches (ohne Lektor)."""
    autor = buch["autor"]
    titel = buch["titel"]

    buch_text = f"\n{'='*60}\n"
    buch_text += f"BUCH: {autor} – {titel}\n"
    buch_text += f"{'='*60}\n"

    # Lektor laden
    if os.path.exists(buch.get("lektor_pfad", "")):
        with open(buch["lektor_pfad"], "r", encoding="utf-8") as f:
            buch_text += f"\n--- LEKTOR-AUFBEREITUNG ---\n{f.read()}\n"

    # Inhaltsanalyse laden
    if os.path.exists(buch.get("inhaltsanalyse_pfad", "")):
        with open(buch["inhaltsanalyse_pfad"], "r", encoding="utf-8") as f:
            buch_text += f"\n--- INHALTSANALYSE ---\n{f.read()}\n"

    # Vernetzung laden
    vernetzung_pfad = buch["lektor_pfad"].replace("01_lektor.md", "03_vernetzung.md")
    if os.path.exists(vernetzung_pfad):
        with open(vernetzung_pfad, "r", encoding="utf-8") as f:
            buch_text += f"\n--- VERNETZUNGSANALYSE ---\n{f.read()}\n"

    # Bericht laden
    bericht_pfad = buch["lektor_pfad"].replace("01_lektor.md", "04_bericht.md")
    if os.path.exists(bericht_pfad):
        with open(bericht_pfad, "r", encoding="utf-8") as f:
            buch_text += f"\n--- GESAMTBERICHT ---\n{f.read()}\n"

    return buch_text


def system_prompt_erstellen(buch_text: str, autor: str, titel: str) -> str:
    """Erstellt den System-Prompt für ein einzelnes Buch."""

    return f"""Du bist ein hochgebildeter, leidenschaftlicher Gesprächspartner und Buchexperte.

Du diskutierst mit Honzele über das Buch "{titel}" von {autor}.

## DEINE WICHTIGSTE REGEL – EISERN EINHALTEN:

Du stützt dich AUSSCHLIESSLICH auf die Analysen die dir unten zur Verfügung stehen.
Du erfindest NICHTS. Du halluzinierst KEINE Zitate, KEINE Seitenzahlen, KEINE Thesen.

Wenn Honzele nach etwas fragt das NICHT in den Analysen steht, sagst du klar:
"Das steht nicht in meinen Analysen."

Wenn du ein Zitat nennst, muss es WÖRTLICH aus den Analysen stammen – mit Seitenangabe.
Wenn du unsicher bist ob ein Zitat stimmt, sagst du es offen.

## WIE DU ANTWORTEST:

- Direkt, klar, auf den Punkt – kein akademisches Geschwafel
- Intellektuell auf Augenhöhe – Honzele ist sehr belesen und analytisch denkend
- Wenn Honzele eine These aufstellt, geh darauf ein – stimm zu, widersprich, ergänze
- Gib Seitenangaben wo immer möglich
- Antworte auf Deutsch

## DEINE WISSENSGRUNDLAGE – NUR DIESE, NICHTS ANDERES:

{buch_text}"""


async def gespraechspartner_starten() -> None:
    """Startet die interaktive Diskussionsrunde."""

    print(f"\n{'='*60}")
    print("  DER GESPRÄCHSPARTNER")
    print("  Dein persönlicher Buchexperte")
    print(f"{'='*60}\n")

    # Buchliste laden
    buecher = bibliothek_laden()

    if not buecher:
        print("  Das Archiv ist noch leer. Bitte zuerst Bücher analysieren.")
        return

    # Buchauswahl
    print("  Welches Buch möchtest du besprechen?\n")
    for i, b in enumerate(buecher, start=1):
        print(f"    {i}. {b['autor']}: {b['titel']}")
    print()

    while True:
        try:
            eingabe = input("  Nummer eingeben: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nAuf Wiedersehen, Honzele!")
            return

        if eingabe.isdigit() and 1 <= int(eingabe) <= len(buecher):
            buch = buecher[int(eingabe) - 1]
            break
        print(f"  Bitte eine Zahl zwischen 1 und {len(buecher)} eingeben.")

    print(f"\n  Analysen werden geladen für: {buch['autor']} – {buch['titel']}...")
    buch_text = buch_laden(buch)
    print(f"  Bereit! ({len(buch_text):,} Zeichen geladen)\n")

    print(f"{'='*60}")
    print("  Du kannst jetzt Fragen stellen oder diskutieren.")
    print("  Tippe 'exit' zum Beenden.")
    print(f"{'='*60}\n")

    system_prompt = system_prompt_erstellen(buch_text, buch["autor"], buch["titel"])

    # Gesprächsverlauf für Kontext
    gespraech = []

    while True:
        try:
            frage = input("Du: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nAuf Wiedersehen, Honzele!")
            break

        if not frage:
            continue

        if frage.lower() in ("exit", "quit", "beenden", "tschüss"):
            print("\nAuf Wiedersehen, Honzele! War ein gutes Gespräch.")
            break

        # Kontext aus bisherigem Gespräch aufbauen
        kontext = ""
        if gespraech:
            kontext = "\n\nBisheriger Gesprächsverlauf:\n"
            for eintrag in gespraech[-6:]:  # Letzte 3 Austausche
                kontext += f"Honzele: {eintrag['frage']}\n"
                kontext += f"Du: {eintrag['antwort'][:500]}...\n\n"

        prompt = f"{kontext}Honzele fragt jetzt: {frage}"

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

        print("\nGesprächspartner: ", end="", flush=True)
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
        antwort = "".join(antwort_teile)
        gespraech.append({"frage": frage, "antwort": antwort})
        print("\n")


if __name__ == "__main__":
    asyncio.run(gespraechspartner_starten())
