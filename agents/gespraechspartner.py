"""
Agent 5: Der Gesprächspartner
Ermöglicht Honzele eine echte Diskussion über die analysierten Bücher.

Wissensgrundlage (alles was vorhanden ist):
  - 01_lektor.md       – Rohaufbereitung
  - 02_inhaltsanalyse.md – Tiefenanalyse
  - 03_vernetzung.md   – Querverbindungen
  - 04_bericht.md      – Gesamtdossier
  - 05_quellen.md      – Quellenliste (mit Prioritätssternen)
  - 06_sekundaerquellen/*.md – fertige Tiefenanalysen einzelner Quellen

Befehle während der Diskussion:
  B    → Abschlussbericht erstellen + optional ins Wiki
  exit → Beenden
"""

import asyncio
import os
import sys
import json
import shutil
import tempfile
from datetime import date
from dotenv import load_dotenv
import anthropic
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import AssistantMessage, TextBlock, ResultMessage, SystemPromptFile

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

BIBLIOTHEK_INDEX = r"E:\Claude_Projekte\Buchanalysen\bibliothek\index.json"
WIKI_RAW_DIR     = r"E:\Claude_Projekte\Wiki_Honzele\raw"
SEKUNDAER_ORDNER = "06_sekundaerquellen"


SYSTEM_PROMPT_DISKUSSION = """Du bist ein hochgebildeter, leidenschaftlicher Gesprächspartner und Buchexperte.

Du diskutierst mit Honzele über das Buch "{titel}" von {autor}.

## DEINE WICHTIGSTE REGEL – EISERN EINHALTEN:

Du stützt dich AUSSCHLIESSLICH auf die Analysen und Quellen die dir unten zur Verfügung stehen.
Du erfindest NICHTS. Du halluzinierst KEINE Zitate, KEINE Seitenzahlen, KEINE Thesen.

Wenn Honzele nach etwas fragt das NICHT in deinen Unterlagen steht, sagst du klar:
"Das steht nicht in meinen Analysen."

Wenn du ein Zitat nennst, muss es WÖRTLICH aus den Analysen stammen – mit Seitenangabe.

## WIE DU MIT DEN QUELLEN UMGEHST:

Du hast Zugriff auf die Quellenliste (05_quellen.md) und evtl. fertige Sekundäranalysen.
Nutze das AKTIV:
- Wenn ein Thema auftaucht, das eine Quelle direkt betrifft → weise darauf hin
- Wenn Honzele nach einem Autor fragt → schau ob er in der Quellenliste steht
- Schlage von dir aus relevante Quellen vor: "Ich sehe in der Quellenliste, dass [Autor/Werk]
  hier direkt zitiert wird – das könnte interessant sein."
- Bei fertigen Sekundäranalysen: nutze die tiefen Erkenntnisse daraus aktiv in der Diskussion

## WIE DU ANTWORTEST:

- Direkt, klar, auf den Punkt – kein akademisches Geschwafel
- Intellektuell auf Augenhöhe – Honzele ist sehr belesen und analytisch denkend
- Wenn Honzele eine These aufstellt, geh darauf ein – stimm zu, widersprich, ergänze
- Gib Seitenangaben wo immer möglich
- Antworte auf Deutsch

## DEINE WISSENSGRUNDLAGE – NUR DIESE, NICHTS ANDERES:

{kontext}"""


SYSTEM_PROMPT_BERICHT = """Du bist ein präziser Dokumentalist.

Du bekommst den Verlauf einer Buchdiskussion zwischen Honzele und seinem Gesprächspartner.
Erstelle daraus einen strukturierten Abschlussbericht.

## STRUKTUR:

### Buch
[Autor, Titel]

### Diskutierte Schwerpunkte
Was wurde in der Diskussion hauptsächlich behandelt? (3-5 Punkte)

### Wichtigste Erkenntnisse
Was hat die Diskussion an neuem Licht oder vertieftem Verständnis gebracht? (konkret, nicht pauschal)

### Honzeles Positionen und Thesen
Was hat Honzele selbst eingebracht, hinterfragt, betont? (seine Perspektive dokumentieren)

### Verbindungen und Querverweise
Welche Verbindungen zu anderen Büchern, Autoren oder Konzepten tauchten auf?

### Offene Fragen
Was blieb offen, was wäre für eine Folgediskussion interessant?

### Empfehlungen
Quellen oder Werke die in der Diskussion als besonders relevant aufgetaucht sind.

---

Sprache: Deutsch. Ton: präzise, klar, lesbar.
Datum der Diskussion: {heute}
Keine Erfindungen – nur was wirklich in der Diskussion vorkam."""


def bibliothek_laden() -> list[dict]:
    with open(BIBLIOTHEK_INDEX, "r", encoding="utf-8") as f:
        return json.load(f).get("buecher", [])


def buch_laden(buch: dict) -> tuple[str, dict]:
    """Lädt alle verfügbaren Analysen eines Buches.

    Gibt den Kontext-Text und eine Statistik zurück (was wurde geladen).
    """
    basis = os.path.dirname(buch["lektor_pfad"])
    sekundaer_dir = os.path.join(basis, SEKUNDAER_ORDNER)

    geladen = {
        "lektor": False,
        "inhaltsanalyse": False,
        "vernetzung": False,
        "bericht": False,
        "quellen": False,
        "sekundaeranalysen": 0,
    }

    kontext = f"\n{'='*60}\n"
    kontext += f"BUCH: {buch['autor']} – {buch['titel']}\n"
    kontext += f"{'='*60}\n"

    # 01 Lektor
    if os.path.exists(buch.get("lektor_pfad", "")):
        with open(buch["lektor_pfad"], "r", encoding="utf-8") as f:
            kontext += f"\n--- LEKTOR-AUFBEREITUNG ---\n{f.read()}\n"
        geladen["lektor"] = True

    # 02 Inhaltsanalyse
    if os.path.exists(buch.get("inhaltsanalyse_pfad", "")):
        with open(buch["inhaltsanalyse_pfad"], "r", encoding="utf-8") as f:
            kontext += f"\n--- INHALTSANALYSE ---\n{f.read()}\n"
        geladen["inhaltsanalyse"] = True

    # 03 Vernetzung
    vernetzung_pfad = buch["lektor_pfad"].replace("01_lektor.md", "03_vernetzung.md")
    if os.path.exists(vernetzung_pfad):
        with open(vernetzung_pfad, "r", encoding="utf-8") as f:
            kontext += f"\n--- VERNETZUNGSANALYSE ---\n{f.read()}\n"
        geladen["vernetzung"] = True

    # 04 Bericht
    bericht_pfad = buch["lektor_pfad"].replace("01_lektor.md", "04_bericht.md")
    if os.path.exists(bericht_pfad):
        with open(bericht_pfad, "r", encoding="utf-8") as f:
            kontext += f"\n--- GESAMTBERICHT ---\n{f.read()}\n"
        geladen["bericht"] = True

    # 05 Quellen
    quellen_pfad = os.path.join(basis, "05_quellen.md")
    if os.path.exists(quellen_pfad):
        with open(quellen_pfad, "r", encoding="utf-8") as f:
            kontext += f"\n--- QUELLENLISTE (05_quellen.md) ---\n{f.read()}\n"
        geladen["quellen"] = True

    # 06 Sekundärquellen-Analysen (alle fertigen Einzelanalysen)
    if os.path.exists(sekundaer_dir):
        for fname in sorted(os.listdir(sekundaer_dir)):
            if fname.startswith("06_") and fname != "06_index.md" and fname.endswith(".md"):
                pfad = os.path.join(sekundaer_dir, fname)
                with open(pfad, "r", encoding="utf-8") as f:
                    kontext += f"\n--- SEKUNDÄRANALYSE: {fname} ---\n{f.read()}\n"
                geladen["sekundaeranalysen"] += 1

    return kontext, geladen


def ladeinfo_anzeigen(buch: dict, geladen: dict) -> None:
    """Zeigt an was geladen wurde."""
    print(f"\n  Geladen für: {buch['autor']} – {buch['titel']}")
    symbole = {
        "lektor":        ("01 Lektor",           geladen["lektor"]),
        "inhaltsanalyse":("02 Inhaltsanalyse",   geladen["inhaltsanalyse"]),
        "vernetzung":    ("03 Vernetzung",        geladen["vernetzung"]),
        "bericht":       ("04 Bericht",           geladen["bericht"]),
        "quellen":       ("05 Quellen",           geladen["quellen"]),
    }
    for key, (name, vorhanden) in symbole.items():
        status = "✓" if vorhanden else "–"
        print(f"    {status}  {name}")

    if geladen["sekundaeranalysen"] > 0:
        print(f"    ✓  06 Sekundäranalysen ({geladen['sekundaeranalysen']} Stück)")
    else:
        print(f"    –  06 Sekundäranalysen (noch keine)")


def abschlussbericht_erstellen(
    gespraech: list[dict],
    autor: str,
    titel: str,
    basis: str,
) -> None:
    """Erstellt einen Abschlussbericht aus dem Gesprächsverlauf."""

    if not gespraech:
        print("\n  Kein Gesprächsverlauf vorhanden – kein Bericht möglich.")
        return

    # Gesprächsverlauf als Text
    verlauf = f"BUCH: {autor} – {titel}\n\nGESPRÄCHSVERLAUF:\n\n"
    for eintrag in gespraech:
        verlauf += f"Honzele: {eintrag['frage']}\n"
        verlauf += f"Gesprächspartner: {eintrag['antwort']}\n\n"

    print(f"\n{'='*60}")
    print(f"  ABSCHLUSSBERICHT wird erstellt...")
    print(f"{'='*60}\n")

    client = anthropic.Anthropic()
    teile = []

    system_prompt = SYSTEM_PROMPT_BERICHT.format(heute=str(date.today()))

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": f"Erstelle den Abschlussbericht für diese Diskussion:\n\n{verlauf}"
        }]
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            teile.append(text)

    print()
    bericht_text = "".join(teile)

    # Lokal speichern
    bericht_datei = f"diskussion_{date.today()}.md"
    bericht_pfad = os.path.join(basis, bericht_datei)

    with open(bericht_pfad, "w", encoding="utf-8") as f:
        f.write(f"# Diskussionsbericht: {titel}\n\n")
        f.write(f"**Autor:** {autor}  \n")
        f.write(f"**Datum:** {date.today()}  \n\n")
        f.write("---\n\n")
        f.write(bericht_text)

    print(f"\n\n  Gespeichert: {bericht_pfad}")
    print(f"  Bitte prüfen ob der Bericht vollständig ist.")

    # Wiki-Transfer anbieten
    print(f"\n{'─'*60}")
    print(f"  WIKI-TRANSFER")
    print(f"  Soll der Bericht nach wiki/raw/ kopiert werden?")
    try:
        antwort = input("  Ins Wiki? (j/n): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return

    if antwort == "j":
        vorschlag = f"Diskussion_{autor.replace(' ', '_')}_{titel[:30].replace(' ', '_')}_{date.today()}.md"
        print(f"  Vorgeschlagener Dateiname: {vorschlag}")
        print(f"  Enter = übernehmen, oder eigenen Namen eingeben:")
        try:
            wiki_name = input("  Dateiname: ").strip()
        except (EOFError, KeyboardInterrupt):
            wiki_name = ""
        if not wiki_name:
            wiki_name = vorschlag

        if os.path.exists(WIKI_RAW_DIR):
            ziel = os.path.join(WIKI_RAW_DIR, wiki_name)
            shutil.copy2(bericht_pfad, ziel)
            print(f"\n  Kopiert nach: wiki/raw/{wiki_name}")
            print(f"  Jetzt im Wiki-Projekt öffnen und injizieren:")
            print(f"  → 'Injiziere {wiki_name}'")
        else:
            print(f"  Wiki raw/-Ordner nicht gefunden: {WIKI_RAW_DIR}")
            print(f"  Bericht liegt lokal: {bericht_pfad}")
    else:
        print(f"  Bericht bleibt lokal: {bericht_pfad}")

    print(f"\n{'='*60}\n")


async def gespraechspartner_starten() -> None:
    """Startet die interaktive Diskussionsrunde."""

    print(f"\n{'='*60}")
    print("  DER GESPRÄCHSPARTNER")
    print("  Dein persönlicher Buchexperte")
    print(f"{'='*60}\n")

    buecher = bibliothek_laden()

    if not buecher:
        print("  Das Archiv ist noch leer. Bitte zuerst Bücher analysieren.")
        return

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

    print(f"\n  Analysen werden geladen...")
    kontext, geladen = buch_laden(buch)
    ladeinfo_anzeigen(buch, geladen)
    print(f"\n  Gesamt: {len(kontext):,} Zeichen geladen")

    basis = os.path.dirname(buch["lektor_pfad"])
    system_prompt = SYSTEM_PROMPT_DISKUSSION.format(
        autor=buch["autor"],
        titel=buch["titel"],
        kontext=kontext,
    )

    print(f"\n{'='*60}")
    print("  Du kannst jetzt Fragen stellen oder diskutieren.")
    print("  'B'    → Abschlussbericht erstellen")
    print("  'exit' → Beenden")
    print(f"{'='*60}\n")

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

        # Abschlussbericht
        if frage.upper() == "B":
            abschlussbericht_erstellen(gespraech, buch["autor"], buch["titel"], basis)
            continue

        # Gesprächskontext aufbauen (letzte 6 Einträge)
        kontext_verlauf = ""
        if gespraech:
            kontext_verlauf = "\n\nBisheriger Gesprächsverlauf:\n"
            for eintrag in gespraech[-6:]:
                kontext_verlauf += f"Honzele: {eintrag['frage']}\n"
                kontext_verlauf += f"Du: {eintrag['antwort'][:500]}...\n\n"

        prompt = f"{kontext_verlauf}Honzele fragt jetzt: {frage}"

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

        # Cursor sauber positionieren nach dem Streaming (Windows-Problem)
        if antwort and not antwort.endswith("\n"):
            sys.stdout.write("\n")
        sys.stdout.write("\n")
        sys.stdout.flush()


if __name__ == "__main__":
    asyncio.run(gespraechspartner_starten())
