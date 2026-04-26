"""
Agent 6: Der Sekundärquellen-Analyst

Diskutiert interaktiv mit Honzele über Quellen aus 05_quellen.md.
Macht Vorschläge, erklärt Zusammenhänge, wartet auf Honzeles Entscheidung.

EISERNE REGEL: 06_sekundaerquellen.md wird NIEMALS automatisch erstellt.
Nur Honzeles explizites Kommando (Taste 'B' + Bestätigung) löst den Bericht aus.
"""

import asyncio
import os
import sys
import json
import tempfile
from datetime import date
from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import AssistantMessage, TextBlock, ResultMessage, SystemPromptFile

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

BIBLIOTHEK_INDEX = r"E:\Claude_Projekte\Buchanalysen\bibliothek\index.json"


SYSTEM_PROMPT_DISKUSSION = """Du bist der Sekundärquellen-Analyst – ein hochspezialisierter Quellenexperte.

Du hast die vollständige Quellenliste (05_quellen.md) und die Analysen des Buches gelesen.

## DEINE AUFGABE:
Diskutiere mit Honzele über die Quellen dieses Buches.
Mache gezielte Vorschläge welche Quellen besonders interessant sind – und warum.
Erkläre welche Rolle eine Quelle in der Argumentation des Autors spielt.

## DEINE EISERNE REGEL – NIEMALS BRECHEN:
Du schreibst KEINEN Bericht. Du erstellst KEINE Datei. Du speicherst NICHTS.
Du diskutierst NUR. Die Entscheidung was berichtet wird, trifft AUSSCHLIESSLICH Honzele.
Kündige NIEMALS selbst an, einen Bericht zu schreiben.

## WIE DU VORSCHLÄGE MACHST:
Präsentiere 3–4 Quellen auf einmal, kurz und konkret. Beispiel:
"Lippmann (1922) ist das Fundament von Mausfelds Manipulationstheorie – ohne ihn
bricht Kapitel 4 zusammen. Interessiert dich das?"

Dann wartest du auf Honzeles Reaktion. Kein Vortrag, kein Monolog.

## WENN HONZELE MEHR WILL:
Gehe tiefer: Was steht in diesem Werk? Was hat der Autor damit belegt?
Welche anderen Bücher in Honzeles Archiv hängen damit zusammen?

## DEIN STIL:
- Direkt, klar, enthusiastisch aber nicht aufdringlich
- Immer auf Deutsch
- Intellektuell auf Augenhöhe – Honzele ist sehr belesen und analytisch denkend
- Kurze Impulse, dann warten – kein Vortrag halten

## DEINE WISSENSGRUNDLAGE – NUR DIESE:
{kontext}"""


SYSTEM_PROMPT_BERICHT = """Du bist der Sekundärquellen-Analyst.

Honzele hat entschieden, für welche Quellen ein Bericht erstellt wird.
Erstelle jetzt einen fundierten Quellenbericht basierend auf dem Gesprächsverlauf.

## STRUKTUR PRO QUELLE:

### [Autor, Jahr] – [Titel]
**Bibliografische Angabe:** (vollständig aus 05_quellen.md)
**Was ist das Werk?** (2–3 Sätze: Gattung, Thema, Bedeutung in der Forschungslandschaft)
**Warum zitiert der Autor es?** (Welche These stützt diese Quelle konkret?)
**Kernbeitrag zur Argumentation** (Was trägt sie zum Gesamtaufbau des Buches bei?)
**Einordnung** (In welcher intellektuellen Tradition steht dieses Werk?)

---

Trenne jede Quelle mit einer Linie (---).
Sprache: Deutsch. Ton: präzise, akademisch, lesbar.
Keine Erfindungen – nur was aus den Analysen hervorgeht oder allgemein bekannt ist.

## WISSENSGRUNDLAGE:
{kontext}"""


def bibliothek_laden() -> list[dict]:
    with open(BIBLIOTHEK_INDEX, "r", encoding="utf-8") as f:
        return json.load(f).get("buecher", [])


def kontext_laden(buch: dict) -> str:
    """Lädt 05_quellen.md + Inhaltsanalyse + Bericht als Wissensgrundlage."""
    basis = os.path.dirname(buch["lektor_pfad"])

    quellen_pfad = os.path.join(basis, "05_quellen.md")
    analyse_pfad = os.path.join(basis, "02_inhaltsanalyse.md")
    bericht_pfad = os.path.join(basis, "04_bericht.md")

    if not os.path.exists(quellen_pfad):
        return ""

    kontext = f"BUCH: {buch['autor']} – {buch['titel']}\n\n"

    with open(quellen_pfad, "r", encoding="utf-8") as f:
        kontext += f"=== QUELLENLISTE (05_quellen.md) ===\n{f.read()}\n\n"

    if os.path.exists(analyse_pfad):
        with open(analyse_pfad, "r", encoding="utf-8") as f:
            kontext += f"=== INHALTSANALYSE ===\n{f.read()}\n\n"

    if os.path.exists(bericht_pfad):
        with open(bericht_pfad, "r", encoding="utf-8") as f:
            kontext += f"=== GESAMTBERICHT ===\n{f.read()}\n\n"

    return kontext


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


async def bericht_erstellen(gespraech: list[dict], kontext: str, ausgabe_pfad: str, autor: str, titel: str) -> None:
    """Erstellt 06_sekundaerquellen.md – NUR nach doppelter Bestätigung durch Honzele."""

    gespraech_text = "\n\nGESPRÄCHSVERLAUF (Honzeles Auswahl und Entscheidungen):\n"
    for eintrag in gespraech:
        gespraech_text += f"Honzele: {eintrag['frage']}\n"
        gespraech_text += f"Analyst: {eintrag['antwort']}\n\n"

    bericht_kontext = kontext + gespraech_text
    system_prompt = SYSTEM_PROMPT_BERICHT.format(kontext=bericht_kontext)

    print(f"\n{'='*60}")
    print(f"  BERICHT WIRD ERSTELLT...")
    print(f"{'='*60}\n")

    bericht_prompt = (
        f"Erstelle den Sekundärquellen-Bericht für '{titel}' von {autor}. "
        f"Berücksichtige dabei die im Gespräch von Honzele ausgewählten und diskutierten Quellen."
    )

    bericht_text = await _agent_fragen(bericht_prompt, system_prompt)

    os.makedirs(os.path.dirname(ausgabe_pfad), exist_ok=True)
    with open(ausgabe_pfad, "w", encoding="utf-8") as f:
        f.write(f"# Sekundärquellen-Analyse: {titel}\n\n")
        f.write(f"**Autor:** {autor}  \n")
        f.write(f"**Erstellt am:** {date.today()}  \n")
        f.write(f"**Grundlage:** 05_quellen.md + 02_inhaltsanalyse.md + 04_bericht.md  \n\n")
        f.write("---\n\n")
        f.write(bericht_text)

    print(f"\n\nGespeichert: {ausgabe_pfad}")
    print(f"  Bitte in der Datei prüfen ob der Bericht vollständig ist.")


async def sekundaerquellen_analyst_starten() -> None:
    """Startet die interaktive Quellendiskussion."""

    print(f"\n{'='*60}")
    print("  DER SEKUNDÄRQUELLEN-ANALYST")
    print("  Quellen entdecken – du entscheidest was berichtet wird")
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
        hat_bericht = os.path.exists(os.path.join(basis, "06_sekundaerquellen.md"))
        markierung = " ✓" if hat_bericht else ""
        print(f"    {i}. {b['autor']}: {b['titel']}{markierung}")
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

    print(f"\n  Lade Quellen und Analysen für: {buch['autor']} – {buch['titel']}...")
    kontext = kontext_laden(buch)

    if not kontext:
        print("  Keine 05_quellen.md gefunden.")
        return

    print(f"  Bereit! ({len(kontext):,} Zeichen geladen)\n")

    basis = os.path.dirname(buch["lektor_pfad"])
    ausgabe_pfad = os.path.join(basis, "06_sekundaerquellen.md")

    system_prompt_diskussion = SYSTEM_PROMPT_DISKUSSION.format(kontext=kontext)

    print(f"{'='*60}")
    print("  Diskutiere jetzt mit dem Quellenanalyst.")
    print("  Tippe 'B' wenn du einen Bericht erstellen möchtest.")
    print("  Tippe 'exit' zum Beenden.")
    print(f"{'='*60}\n")

    # Eröffnung: Agent macht erste Vorschläge ohne Aufforderung
    print("Analyst: ", end="", flush=True)
    eroeffnung = await _agent_fragen(
        f"Analysiere die Quellenliste von '{buch['titel']}' von {buch['autor']} "
        f"und stelle Honzele 3–4 besonders interessante Quellen vor. "
        f"Kurz und konkret, dann warte auf seine Reaktion.",
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

        # Bericht-Trigger – doppelte Absicherung
        if eingabe.upper() == "B":
            print(f"\n  Bericht wird gespeichert in:")
            print(f"  {ausgabe_pfad}")
            bestaetigung = input("\n  Jetzt erstellen? (j/n): ").strip().lower()
            if bestaetigung == "j":
                await bericht_erstellen(
                    gespraech, kontext, ausgabe_pfad, buch["autor"], buch["titel"]
                )
            else:
                print("  Abgebrochen – wir diskutieren weiter.\n")
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
