"""
Agent 2: Der Inhaltsanalyst
Analysiert Kernthesen, Argumentationsstruktur, Methodik und ideologisches Fundament.
Liest die Lektor-Aufbereitung (01_lektor.md) und erstellt eine Tiefenanalyse.
Ergebnis: analysen/<Autor>/<Buch>/02_inhaltsanalyse.md
"""

import asyncio
import os
import sys
import tempfile
from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import AssistantMessage, TextBlock, ResultMessage, SystemPromptFile

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()


SYSTEM_PROMPT = """Du bist ein hochspezialisierter Literatur- und Sachbuchanalyst mit Expertise in politischer Wissenschaft, Geschichte und Ideologieanalyse.

Du bekommst die aufbereitete Zusammenfassung eines Sachbuches und erstellst eine professionelle Tiefenanalyse.

Deine Analyse umfasst folgende Abschnitte:

---

## 1. KERNTHESEN
Liste die 3-5 zentralen Thesen des Autors auf.
Jede These: prägnant formuliert + 2-3 Sätze Erläuterung wie der Autor sie belegt.

## 2. ARGUMENTATIONSSTRUKTUR
Wie baut der Autor seinen Fall auf?
- Welche Strategie verfolgt er? (historisch-genetisch / komparativ / dialektisch / rhetorisch...)
- Wie setzt er seine Kapitel zueinander in Beziehung?
- Führt er den Leser schrittweise zu einer Schlussfolgerung – oder argumentiert er von der These aus rückwärts?

## 3. QUELLEN & METHODIK
- Welche Arten von Quellen nutzt der Autor? (Primärquellen, Historiker, Journalisten, Zeitzeugen...)
- Wie belastbar ist die Beweisführung?
- Gibt es Quellen die er bevorzugt oder meidet?

## 4. IDEOLOGISCHES FUNDAMENT
- Welches Weltbild liegt dem Buch zugrunde?
- Welche politische/moralische Haltung vertritt der Autor?
- Wo ist er explizit parteiisch – und wo versucht er neutral zu wirken?

## 5. STÄRKEN DER ARGUMENTATION
Was macht das Buch besonders überzeugend?
Konkrete Beispiele mit Seitenangaben.

## 6. BLINDE FLECKEN & SCHWACHSTELLEN
Was lässt der Autor aus? Wo könnte man widersprechen?
Keine Verunglimpfung – sachliche Analyse der Grenzen des Werkes.

## 7. EINORDNUNG
- In welcher Tradition steht das Buch?
- Mit welchen anderen Werken/Autoren ist es zu vergleichen?
- Was ist der Beitrag dieses Buches zur Debatte?

---

Sprache: Deutsch. Ton: akademisch aber lesbar. Keine Wertung des Inhalts – nur Analyse der Argumentation."""


async def inhaltsanalyst_analysieren(lektor_pfad: str, ausgabe_pfad: str) -> None:
    """Liest die Lektor-Aufbereitung und erstellt eine Tiefenanalyse."""

    buch_name = os.path.basename(os.path.dirname(lektor_pfad))

    print(f"\n{'='*60}")
    print(f"INHALTSANALYST startet: {buch_name}")
    print(f"{'='*60}\n")

    # Lektor-Aufbereitung einlesen
    print("Lektor-Aufbereitung wird geladen...")
    with open(lektor_pfad, "r", encoding="utf-8") as f:
        lektor_text = f.read()
    print(f"  {len(lektor_text):,} Zeichen geladen\n")

    # System-Prompt + Lektor-Text als Datei (Windows-Limit umgehen)
    system_prompt_inhalt = f"""{SYSTEM_PROMPT}

## LEKTOR-AUFBEREITUNG DES BUCHES "{buch_name}":

{lektor_text}"""

    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".txt", delete=False
    ) as tmp:
        tmp.write(system_prompt_inhalt)
        tmp_pfad = tmp.name

    options = ClaudeAgentOptions(
        system_prompt=SystemPromptFile(type="file", path=tmp_pfad),
        allowed_tools=[],
        permission_mode="acceptEdits",
        max_turns=3,
    )

    print("Inhaltsanalyst arbeitet...\n")
    print("-" * 60)

    ergebnis_teile = []
    kosten = 0.0

    async for message in query(
        prompt=f'Erstelle die Tiefenanalyse für "{buch_name}" gemäß deinen Anweisungen. Stütze dich auf konkrete Stellen mit Seitenangaben.',
        options=options
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="", flush=True)
                    ergebnis_teile.append(block.text)
        elif isinstance(message, ResultMessage):
            if message.is_error:
                print(f"\n[Fehler] Agent beendet mit Fehler: {message.subtype}")
            elif message.total_cost_usd is not None:
                kosten = message.total_cost_usd
                print(f"\n\n[Kosten: ${kosten:.4f} | Durchläufe: {message.num_turns}]")

    print("\n" + "-" * 60)
    os.unlink(tmp_pfad)

    # Ergebnis speichern
    ergebnis = "".join(ergebnis_teile)
    os.makedirs(os.path.dirname(ausgabe_pfad), exist_ok=True)
    with open(ausgabe_pfad, "w", encoding="utf-8") as f:
        f.write(f"# Inhaltsanalyse: {buch_name}\n\n")
        f.write(f"**Grundlage:** 01_lektor.md  \n")
        f.write(f"**Analysiert am:** {__import__('datetime').date.today()}  \n\n")
        f.write("---\n\n")
        f.write(ergebnis)

    print(f"\nGespeichert: {ausgabe_pfad}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    LEKTOR_PFAD = r"E:\Claude_Projekte\Buchanalysen\analysen\Michael_Luders\Krieg_ohne_Ende\01_lektor.md"
    AUSGABE     = r"E:\Claude_Projekte\Buchanalysen\analysen\Michael_Luders\Krieg_ohne_Ende\02_inhaltsanalyse.md"
    asyncio.run(inhaltsanalyst_analysieren(LEKTOR_PFAD, AUSGABE))
