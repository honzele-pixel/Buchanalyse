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

import os
import re
import shutil
import sys
import json
from datetime import date
from dotenv import load_dotenv
import anthropic

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

BIBLIOTHEK_INDEX    = r"E:\Claude_Projekte\Buchanalysen\bibliothek\index.json"
QUALITAETS_REFERENZ = r"E:\Claude_Projekte\Buchanalysen\analysen\Rainer_Mausfeld\Hegemonie_oder_Untergang\06_sekundaerquellen\06_mirowski_2015.md"
WIKI_RAW_DIR        = r"E:\Claude_Projekte\Wiki_Honzele\raw"
SEKUNDAER_ORDNER    = "06_sekundaerquellen"

CLIENT = anthropic.Anthropic()


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

Erstelle eine tiefe Einzelanalyse der besprochenen Quelle.
Die QUALITÄTS-REFERENZ unten zeigt das Niveau – erreiche es, kopiere es nicht.

## PFLICHTANFORDERUNGEN – KEINE KÜRZUNGEN:

### Schicht 1 muss mindestens 5 eigene Unterabschnitte haben:
Jedes Schlüsselkonzept des Werkes bekommt seinen eigenen ### Abschnitt mit Titel.
Nicht allgemein zusammenfassen – jedes Konzept einzeln und präzise erklären.
Beispiel: nicht "Mirowski erklärt drei Dinge" sondern "### Das Gedankenkollektiv – Mirowskis Schlüsselkonzept" → dann 200+ Wörter nur dazu.

### Schicht 2 muss konkret und asymmetrisch sein:
Nicht "Werk A stützt Werk B" – sondern: was genau fehlt im Primärwerk, was die Sekundärquelle liefert.
Formuliere es als intellektuelle Lücke: "Mausfeld beschreibt das WAS, Mirowski das WIE."
Nutze Seitenangaben aus dem Primärwerk wo vorhanden.

### Schicht 3 muss Wiki-Links im Format [[Seitenname]] enthalten:
Für jede bestehende Wiki-Seite die angereichert werden kann: [[Seitenname]] mit konkreter Begründung.
Für neue Seiten die entstehen könnten: [[Vorgeschlagene_Seite]] mit Begründung.
Empfehlung an Wiki-Kurator: JA / NEIN / BEDINGT – mit einem Satz Begründung.

### Steckbrief ist Pflicht:
Wer ist der Autor? (Jahrgang, akademische Heimat, Forschungsfeld)
Wann und warum entstand das Werk? (historischer Entstehungskontext)

---

## VOLLSTÄNDIGE STRUKTUR:

# [Autor] – [Titel] ([Jahr])

**Bibliografische Angabe:** [vollständig]
**Primärkontext:** Zitiert in: [Primärautor] – [Primärtitel]
**Analysiert:** {heute}
**Modell:** claude-opus-4-6

---

## Steckbrief
[Autor-Bio + Entstehungskontext des Werkes, 100–200 Wörter]

---

## Schicht 1: Was das Werk argumentiert

### [Unterabschnitt 1: Grundthese / Das zentrale Paradox]
[200+ Wörter]

### [Unterabschnitt 2: Erstes Schlüsselkonzept]
[200+ Wörter]

### [Unterabschnitt 3: Zweites Schlüsselkonzept]
[200+ Wörter]

### [Unterabschnitt 4: Drittes Schlüsselkonzept]
[200+ Wörter]

### [Unterabschnitt 5: Mechanismus / Organisationslogik]
[200+ Wörter]

---

## Schicht 2: Die Brücke zum Primärwerk

### Warum [Primärautor] diese Quelle braucht – die analytische Lücke
[Was fehlt im Primärwerk, was die Sekundärquelle füllt – 200+ Wörter]

### [Spezifischer Berührungspunkt 1]
[Konkrete These im Primärwerk + was die Sekundärquelle dazu beisteuert]

### [Spezifischer Berührungspunkt 2]
[Konkrete These im Primärwerk + was die Sekundärquelle dazu beisteuert]

### Was die Sekundärquelle dem Primärwerk schuldet – und was nicht
[Grenzen der Verbindung – 100+ Wörter]

---

## Schicht 3: Verbindung zu Honzeles Kanon

### Hesiod-Linse / Pleonexia
[Wie verbindet sich das Werk mit Pleonexia als Ur-Motor der Macht?]

### Diagnoselinie
[Welche Stelle in der Kette Hesiod → Solon → Thukydides → ... → Mausfeld füllt dieses Werk?]

### Hirten-Herden-Metapher / Melier-Dialog
[Verbindung wenn vorhanden]

---

## Wiki-Potenzial

### Bestehende Seiten die angereichert werden sollten
- **[[Seitenname]]** – [konkrete Begründung was diese Quelle beisteuert]
- **[[Seitenname]]** – [konkrete Begründung]

### Neue Seiten die entstehen könnten
- **[[Vorgeschlagene_Seite]]** – [Begründung warum diese Seite ein eigenständiges Konzept wäre]

### Empfehlung an Wiki-Kurator
**[JA / NEIN / BEDINGT]** – [Ein Satz mit Begründung]

---

## Status
**Analysiert:** {heute}
**Wiki-Übergabe:** ausstehend

---

Sprache: Deutsch. Ton: präzise, akademisch, lesbar.
Keine Erfindungen – nur was aus den Analysen hervorgeht oder allgemein bekannt ist.
Wenn etwas auf eigenem Wissen basiert (nicht aus den Analysen), markiere es: *(Nach Claudes Wissen – nicht aus dem PDF.)*

## QUALITÄTS-REFERENZ – DIESES NIVEAU ERREICHEN:
{beispiel}

## WISSENSGRUNDLAGE:
{kontext}"""


# ─────────────────────────────────────────────
#  HILFSFUNKTIONEN
# ─────────────────────────────────────────────

def index_aus_quellen_generieren(basis: str, autor: str, titel: str) -> bool:
    """Generiert 06_index.md automatisch aus der Prioritätsbewertung in 05_quellen.md."""
    quellen_pfad = os.path.join(basis, "05_quellen.md")
    sekundaer_dir = os.path.join(basis, SEKUNDAER_ORDNER)
    index_pfad = os.path.join(sekundaer_dir, "06_index.md")

    if not os.path.exists(quellen_pfad):
        return False

    with open(quellen_pfad, "r", encoding="utf-8") as f:
        quellen_text = f.read()

    if "★" not in quellen_text:
        return False

    print("  Kein 06_index.md gefunden – wird aus Prioritätsbewertung generiert...")

    response = CLIENT.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": f"""Hier ist die 05_quellen.md für "{autor}: {titel}":

{quellen_text}

Erstelle daraus einen 06_index.md in exakt diesem Format:

# Sekundärquellen-Index: {titel}
**Primärautor:** {autor}
**Erstellt:** {date.today()}
**Stand:** {date.today()}

---

## Prioritätsliste

| Quelle | Priorität | Status | Wiki-Potenzial | Notiz |
|---|---|---|---|---|
[alle Quellen aus der Prioritätsbewertungs-Tabelle, eine pro Zeile]

## Legende
★★★★★ = Höchste Priorität
★★★★☆ = Hohe Priorität
★★★☆☆ = Mittlere Priorität
★★☆☆☆ = Niedrige Priorität
★☆☆☆☆ = Minimal

REGELN:
- Übernimm alle Quellen aus der Prioritätsbewertungs-Tabelle
- Status immer "→ offen" (nichts ist noch analysiert)
- ★★★★★ bleibt ★★★★★ | ★★★★ wird ★★★★☆ | ★★★ wird ★★★☆☆ | ★★ wird ★★☆☆☆ | ★ wird ★☆☆☆☆
- Wiki-Potenzial: "hoch" / "mittel" / "niedrig" – einschätzen
- Notiz: 1 kurzer Satz aus der Begründungsspalte
- Nur die Tabellen-Inhalte ausgeben – kein erklärender Text drumherum"""
        }]
    )

    index_text = response.content[0].text
    os.makedirs(sekundaer_dir, exist_ok=True)

    with open(index_pfad, "w", encoding="utf-8") as f:
        f.write(index_text)

    print(f"  06_index.md erstellt: {index_pfad}")
    return True


def eingabe(prompt: str) -> str:
    """Ersatz für input() – garantiert sauberen Cursor auf Windows nach Streaming."""
    sys.stdout.write(prompt)
    sys.stdout.flush()
    try:
        return sys.stdin.readline().rstrip("\n").rstrip("\r")
    except (EOFError, KeyboardInterrupt):
        raise KeyboardInterrupt


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

    if os.path.exists(index_pfad):
        with open(index_pfad, "r", encoding="utf-8") as f:
            kontext += f"=== PRIORITÄTS-INDEX (06_index.md) ===\n{f.read()}\n\n"

    if os.path.exists(sekundaer_dir):
        for fname in sorted(os.listdir(sekundaer_dir)):
            if fname.startswith("06_") and fname != "06_index.md" and fname.endswith(".md"):
                pfad = os.path.join(sekundaer_dir, fname)
                with open(pfad, "r", encoding="utf-8") as f:
                    kontext += f"=== BEREITS ANALYSIERT: {fname} ===\n{f.read()}\n\n"

    with open(quellen_pfad, "r", encoding="utf-8") as f:
        kontext += f"=== QUELLENLISTE (05_quellen.md) ===\n{f.read()}\n\n"

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


def api_antwort(
    messages: list[dict],
    system: str,
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 2048,
) -> str:
    """Direkte Anthropic-API mit Streaming. Gibt den vollständigen Antworttext zurück."""
    antwort_teile = []
    with CLIENT.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            antwort_teile.append(text)

    antwort = "".join(antwort_teile)
    if antwort and not antwort.endswith("\n"):
        sys.stdout.write("\n")
    sys.stdout.write("\n")
    sys.stdout.flush()
    return antwort


def einzelanalyse_erstellen(
    messages: list[dict],
    kontext: str,
    basis: str,
    buch_autor: str,
    buch_titel: str,
) -> None:
    """Erstellt eine Einzelanalyse pro Quelle – NUR nach doppelter Bestätigung."""

    print("\n  Welche Quelle soll analysiert werden?")
    print("  Beispiel: 'Reich 1933' oder 'Fanon 1969'")
    try:
        quellen_name = eingabe("  Quelle: ").strip()
    except KeyboardInterrupt:
        print("\n  Abgebrochen.")
        return

    if not quellen_name:
        print("  Kein Name angegeben – abgebrochen.")
        return

    dateiname = "06_" + re.sub(r"[^a-z0-9]+", "_", quellen_name.lower()).strip("_") + ".md"
    sekundaer_dir = os.path.join(basis, SEKUNDAER_ORDNER)
    ausgabe_pfad = os.path.join(sekundaer_dir, dateiname)

    print(f"\n  Analyse wird gespeichert als: {dateiname}")
    try:
        bestaetigung = eingabe("  Jetzt erstellen? (j/n): ").strip().lower()
    except KeyboardInterrupt:
        return

    if bestaetigung != "j":
        print("  Abgebrochen – wir diskutieren weiter.\n")
        return

    beispiel = ""
    if os.path.exists(QUALITAETS_REFERENZ):
        with open(QUALITAETS_REFERENZ, "r", encoding="utf-8") as f:
            beispiel = f.read()

    # Gesprächsverlauf aus den messages extrahieren (letzte 10 Einträge)
    gespraech_text = "\n\nGESPRÄCHSVERLAUF (Honzeles Fokus und Entscheidungen):\n"
    for msg in messages[-10:]:
        rolle = "Honzele" if msg["role"] == "user" else "Analyst"
        inhalt = msg["content"] if isinstance(msg["content"], str) else str(msg["content"])
        gespraech_text += f"{rolle}: {inhalt[:600]}\n\n"

    system_bericht = SYSTEM_PROMPT_BERICHT.format(
        kontext=kontext + gespraech_text,
        beispiel=beispiel,
        heute=str(date.today()),
    )

    print(f"\n{'='*60}")
    print(f"  ANALYSE WIRD ERSTELLT: {quellen_name}")
    print(f"{'='*60}\n")

    analyse_messages = [{
        "role": "user",
        "content": (
            f"Erstelle die Tiefenanalyse für '{quellen_name}' als Sekundärquelle "
            f"von '{buch_titel}' ({buch_autor}). "
            f"Berücksichtige den Gesprächsverlauf und Honzeles Fokus."
        )
    }]

    analyse_text = api_antwort(
        analyse_messages,
        system_bericht,
        model="claude-sonnet-4-6",
        max_tokens=8000,
    )

    os.makedirs(sekundaer_dir, exist_ok=True)
    with open(ausgabe_pfad, "w", encoding="utf-8") as f:
        f.write(analyse_text)

    print(f"\n\nGespeichert: {ausgabe_pfad}")
    print(f"  Bitte in der Datei prüfen ob die Analyse vollständig ist.")

    index_aktualisieren(basis, quellen_name, dateiname)

    print(f"\n{'─'*60}")
    print(f"  WIKI-INJEKTION")
    print(f"  Soll diese Analyse nach wiki/raw/ kopiert werden?")
    try:
        wiki_antwort = eingabe("  Ins Wiki? (j/n): ").strip().lower()
    except KeyboardInterrupt:
        return

    if wiki_antwort == "j":
        vorschlag = re.sub(r"[^a-zA-Z0-9]+", "_", quellen_name).strip("_")
        vorschlag = f"{vorschlag}_Sekundaeranalyse.md"
        print(f"  Vorgeschlagener Dateiname: {vorschlag}")
        print(f"  Enter = übernehmen, oder eigenen Namen eingeben:")
        try:
            wiki_name = eingabe("  Dateiname: ").strip()
        except KeyboardInterrupt:
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

def sekundaerquellen_analyst_starten() -> None:
    """Startet die interaktive Quellendiskussion."""

    print(f"\n{'='*60}")
    print("  DER SEKUNDÄRQUELLEN-ANALYST")
    print("  Index-gesteuert · Einzelanalysen · Wiki-ready")
    print(f"{'='*60}\n")

    buecher = bibliothek_laden()

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
        anzahl = 0
        if os.path.exists(sekundaer_dir):
            anzahl = len([
                f for f in os.listdir(sekundaer_dir)
                if f.startswith("06_") and f != "06_index.md" and f.endswith(".md")
            ])
        status = (
            f" [Index ✓, {anzahl} Analyse(n)]" if hat_index
            else (" [kein Index]" if anzahl == 0 else f" [{anzahl} Analyse(n)]")
        )
        print(f"    {i}. {b['autor']}: {b['titel']}{status}")
    print()

    while True:
        try:
            auswahl = eingabe("  Nummer eingeben: ").strip()
        except KeyboardInterrupt:
            print("\n\nAuf Wiedersehen, Honzele!")
            return
        if auswahl.isdigit() and 1 <= int(auswahl) <= len(buecher_mit_quellen):
            buch = buecher_mit_quellen[int(auswahl) - 1]
            break
        print(f"  Bitte eine Zahl zwischen 1 und {len(buecher_mit_quellen)} eingeben.")

    basis = os.path.dirname(buch["lektor_pfad"])
    sekundaer_dir_check = os.path.join(basis, SEKUNDAER_ORDNER)
    hat_index = os.path.exists(os.path.join(sekundaer_dir_check, "06_index.md"))
    if not hat_index:
        index_generiert = index_aus_quellen_generieren(basis, buch["autor"], buch["titel"])
        if not index_generiert:
            print("  Kein Index und keine Prioritätsbewertung in 05_quellen.md gefunden.")
            print("  Bitte zuerst den Quellenextraktor (Modus 4) ausführen.")

    print(f"\n  Lade Kontext für: {buch['autor']} – {buch['titel']}...")
    kontext = kontext_laden(buch)

    if not kontext:
        print("  Keine 05_quellen.md gefunden.")
        return

    print(f"  Bereit! ({len(kontext):,} Zeichen geladen)\n")

    system_diskussion = SYSTEM_PROMPT_DISKUSSION.format(kontext=kontext)

    print(f"{'='*60}")
    print("  Diskutiere mit dem Quellenanalyst.")
    print("  'B' → Einzelanalyse erstellen")
    print("  'exit' → Beenden")
    print(f"{'='*60}\n")

    # Echter Multi-Turn Verlauf – eine Konversation, keine neuen Sessions
    messages: list[dict] = []

    eroeffnungs_prompt = (
        f"Schaue in den Prioritäts-Index (06_index.md) für '{buch['titel']}' von {buch['autor']}. "
        f"Präsentiere Honzele die 2–3 wichtigsten noch offenen Quellen (★★★★★ zuerst). "
        f"Kurz und konkret mit Stern-Bewertung, dann warte auf seine Reaktion. "
        f"Falls kein Index vorhanden: analysiere die 05_quellen.md und schlage die wichtigsten vor."
    )
    messages.append({"role": "user", "content": eroeffnungs_prompt})

    print("Analyst: ", end="", flush=True)
    eroeffnung = api_antwort(messages, system_diskussion)
    messages.append({"role": "assistant", "content": eroeffnung})

    while True:
        try:
            benutzer_eingabe = eingabe("Du: ").strip()
        except KeyboardInterrupt:
            print("\n\nAuf Wiedersehen, Honzele!")
            break

        if not benutzer_eingabe:
            continue

        if benutzer_eingabe.lower() in ("exit", "quit", "beenden"):
            print("\nAuf Wiedersehen, Honzele!")
            break

        if benutzer_eingabe.upper() == "B":
            einzelanalyse_erstellen(
                messages, kontext, basis, buch["autor"], buch["titel"]
            )
            # Kontext + System-Prompt neu laden (neue Analyse ist jetzt drin)
            kontext = kontext_laden(buch)
            system_diskussion = SYSTEM_PROMPT_DISKUSSION.format(kontext=kontext)
            continue

        messages.append({"role": "user", "content": benutzer_eingabe})

        print("\nAnalyst: ", end="", flush=True)
        antwort = api_antwort(messages, system_diskussion)
        messages.append({"role": "assistant", "content": antwort})


if __name__ == "__main__":
    sekundaerquellen_analyst_starten()
