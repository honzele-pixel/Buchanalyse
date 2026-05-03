"""
Agent: Quellenextraktor

Extrahiert alle Quellen und Literaturangaben aus einem PDF-Buch.
Ergebnis: analysen/<Autor>/<Buch>/05_quellen.md

Strategie:
1. PDF lesen (PyMuPDF) – letztes 40% priorisieren (dort sitzt das Literaturverzeichnis)
2. Claude extrahiert alle Quellentypen: Literaturverzeichnis, Fußnoten, Empfehlungen, URLs
3. Zweiter Durchlauf: Prioritätssterne vergeben (★ bis ★★★★★) für Agent 6
"""

import os
import sys
import json
from datetime import date
import fitz  # PyMuPDF
import anthropic
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

BIBLIOTHEK_INDEX = r"E:\Claude_Projekte\Buchanalysen\bibliothek\index.json"
QUELLEN_ANTEIL   = 0.40  # Letztes 40% des PDFs für Quellensuche


SYSTEM_PROMPT_EXTRAKTION = """Du bist ein präziser Quellenanalyst.

Du bekommst den Text des hinteren Teils eines Buches.
Deine Aufgabe: Extrahiere ALLE Quellenangaben vollständig und strukturiert.

## WAS DU SUCHST:

1. **Literaturverzeichnis** – klassische Bibliografie am Buchende
2. **Endnoten / Anmerkungen** – nummerierte Belege (Abschnitte wie "Anmerkungen", "Endnoten", "Notes")
3. **Empfohlene Literatur** – "Weiterführende Lektüre", "Bibliografische Empfehlungen", "Zur Vertiefung"
4. **Webseiten & Online-Quellen** – alle URLs, Webseiten, Datenbanken (besonders hervorheben!)
5. **Eigene Webseite des Autors** – falls das Buch auf eine begleitende Website verweist

## AUSGABE-FORMAT (nur vorhandene Abschnitte):

### Literaturverzeichnis
Vollständige bibliografische Angaben, eine pro Zeile, sortiert wie im Original.

### Endnoten / Anmerkungen
Nummeriert wie im Original, mit vollständiger Quellenangabe.

### Weiterführende Literatur / Empfehlungen
Vollständige Angaben.

### Webseiten & Online-Quellen
Format: **[Beschreibung]:** [URL]
(Dieser Abschnitt ist für Honzele besonders wichtig – er kann diese Seiten direkt besuchen!)

## WICHTIGE REGELN:
- Vollständig extrahieren – keine Kürzungen, keine Auslassungen
- Exakt so wie im Original – keine eigene Interpretation
- Seitenzahlen angeben wo erkennbar (z.B. "Seiten 174–185")
- Wenn kein klassisches Literaturverzeichnis: "Kein klassisches Literaturverzeichnis – [was stattdessen gefunden]"
- Sprache: Deutsch für Beschreibungen, Originaltitel beibehalten"""


SYSTEM_PROMPT_BEWERTUNG = """Du bist der Sekundärquellen-Analyst – Spezialist für Honzeles Wissensbibliothek.

Du bekommst eine extrahierte Quellenliste aus einem Buch.
Deine Aufgabe: Vergib Prioritätssterne für die wichtigsten Quellen – als Startpunkt für Agent 6.

## BEWERTUNGSKRITERIEN:

**★★★★★ Absolut zentral** – wenn EINE dieser Bedingungen zutrifft:
- Autor gehört zu Honzeles Kanon: Chomsky, Fanon, Arendt, Foucault, Bourdieu, Gramsci,
  Adorno, Horkheimer, Marcuse, Lüders, Mausfeld, Ganser, Guerot, Kant, Thukydides,
  Zinn, Said, Blum, Harvey, Wallerstein, Brecht, Reich, Fromm, Milgram, Asch, Orwell
- Werk ist DAS Standardwerk für: Imperialismus, Propaganda, Demokratiekritik,
  Geopolitik, Massenpsychologie, Kolonialismus, Machtanalyse, Kriege
- Das Werk stützt eine KERNTHESE des Primärwerks (erkennbar an häufiger Zitation)

**★★★★ Hochrelevant:**
- Wissenschaftliches Standardwerk im Themenfeld
- Direkte Verbindung zu Honzeles Themen (Pleonexia, Hirten-Herden, Melier-Dialog, Krieg)
- Kritische Denker die Honzele noch nicht kennt, aber kennen sollte

**★★★ Gut und relevant:**
- Wichtige Kontextquelle, ergänzt das Bild
- Fachlich solide, für tieferes Verständnis nützlich

**★★ Spezifisch:**
- Belegt Detailaussagen, wichtig für das Buch aber kaum Anknüpfung an Kanon

**★ Vollständigkeit:**
- Randquelle, Spezialthema

## AUSGABE-FORMAT:

Zuerst die Tabelle (Top 20 sortiert nach Priorität):

| Priorität | Quelle | Warum für Honzele? |
|---|---|---|
| ★★★★★ | Chomsky (1992): Deterring Democracy | Kernwerk für Demokratiekritik, direkt im Kanon |
| ★★★★ | ... | ... |

Dann:

**Sofort mit Agent 6 starten (★★★★★):** [Namen aufzählen]
**Nächste Runde (★★★★):** [Namen aufzählen]

Sprache: Deutsch. Kurz und präzise."""


def pdf_lesen(pdf_pfad: str) -> tuple[str, int, str]:
    """Liest PDF vollständig, gibt Volltext, Seitenzahl und letztes 40% zurück."""
    doc = fitz.open(pdf_pfad)
    seitenanzahl = len(doc)
    seiten = []

    for nr, seite in enumerate(doc, start=1):
        text = seite.get_text()
        if text.strip():
            seiten.append(f"[Seite {nr}]\n{text}")

    doc.close()
    volltext = "\n\n".join(seiten)

    # Letztes 40% für Quellensuche (Literaturverzeichnis sitzt meist dort)
    startpunkt = int(len(volltext) * (1 - QUELLEN_ANTEIL))
    quellen_bereich = volltext[startpunkt:]

    return volltext, seitenanzahl, quellen_bereich


def quellen_extrahieren(quellen_bereich: str, buch_name: str) -> str:
    """Schritt 1: Claude extrahiert alle Quellenangaben aus dem Quellenbereich."""
    client = anthropic.Anthropic()
    teile = []

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=SYSTEM_PROMPT_EXTRAKTION,
        messages=[{
            "role": "user",
            "content": (
                f'Hier ist der hintere Teil des Buches "{buch_name}" (letztes 40%).\n\n'
                f'Bitte extrahiere ALLE Quellenangaben vollständig:\n\n{quellen_bereich}'
            )
        }]
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            teile.append(text)

    print()
    return "".join(teile)


def sterne_vergeben(quellen_text: str, autor: str, titel: str) -> str:
    """Schritt 2: Claude bewertet die Quellen mit Prioritätssternen für Agent 6."""
    client = anthropic.Anthropic()
    teile = []

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT_BEWERTUNG,
        messages=[{
            "role": "user",
            "content": (
                f'Quellen aus: **{autor} – {titel}**\n\n'
                f'{quellen_text}\n\n'
                f'Bitte Prioritätssterne vergeben.'
            )
        }]
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            teile.append(text)

    print()
    return "".join(teile)


def quellenextraktor_starten(buch: dict, ausgabe_pfad: str) -> None:
    """Hauptfunktion: Extrahiert Quellen aus einem Buch-PDF und speichert 05_quellen.md."""

    pdf_pfad = buch["pdf_pfad"]
    autor    = buch["autor"]
    titel    = buch["titel"]
    buch_name = os.path.splitext(os.path.basename(pdf_pfad))[0]

    print(f"\n{'='*60}")
    print(f"  QUELLENEXTRAKTOR")
    print(f"  {autor}: {titel}")
    print(f"{'='*60}\n")

    # Schritt 1: PDF lesen
    print("  Schritt 1: PDF wird gelesen...")
    volltext, seitenanzahl, quellen_bereich = pdf_lesen(pdf_pfad)
    print(f"  {seitenanzahl} Seiten | {len(volltext):,} Zeichen gesamt")
    print(f"  Quellenbereich (letzte 40%): {len(quellen_bereich):,} Zeichen\n")

    # Schritt 2: Quellen extrahieren
    print("  Schritt 2: Quellenextraktion läuft...\n")
    print("-" * 60)
    quellen_roh = quellen_extrahieren(quellen_bereich, buch_name)
    print("-" * 60)

    # Schritt 3: Sterne vergeben
    print("\n  Schritt 3: Prioritätsbewertung für Agent 6...\n")
    print("-" * 60)
    sterne_tabelle = sterne_vergeben(quellen_roh, autor, titel)
    print("-" * 60)

    # Schritt 4: Speichern
    os.makedirs(os.path.dirname(ausgabe_pfad), exist_ok=True)

    with open(ausgabe_pfad, "w", encoding="utf-8") as f:
        f.write(f"# Quellen: {titel}\n\n")
        f.write(f"**Autor:** {autor}  \n")
        f.write(f"**Extrahiert am:** {date.today()}  \n")
        f.write(f"**PDF-Quelle:** {pdf_pfad}  \n")
        f.write(f"**Seiten gesamt:** {seitenanzahl}  \n")
        f.write("\n---\n\n")
        f.write(quellen_roh)
        f.write("\n\n---\n\n")
        f.write("## Prioritätsbewertung für Agent 6\n\n")
        f.write(sterne_tabelle)

    print(f"\n\n  Gespeichert: {ausgabe_pfad}")
    print(f"  Bitte in der Datei prüfen ob die Quellen vollständig erfasst sind.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Direktstart zum Testen
    import json

    with open(BIBLIOTHEK_INDEX, "r", encoding="utf-8") as f:
        buecher = json.load(f).get("buecher", [])

    if buecher:
        b = buecher[0]
        basis = os.path.dirname(b["lektor_pfad"])
        ausgabe = os.path.join(basis, "05_quellen.md")
        buch_dict = {
            "autor":    b["autor"],
            "titel":    b["titel"],
            "pdf_pfad": b.get("pdf_pfad", ""),
        }
        quellenextraktor_starten(buch_dict, ausgabe)
