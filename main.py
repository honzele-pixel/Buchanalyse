"""
Buchanalyse-System – Hauptprogramm

Zwei Modi:
  1. Buch analysieren  – alle 4 Agenten laufen automatisch durch
  2. Diskutieren       – mit dem Gesprächspartner über Bücher reden

Verwendung: python main.py
"""

import asyncio
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

import json

from agents.lektor                     import lektor_analysieren
from agents.inhaltsanalyst             import inhaltsanalyst_analysieren
from agents.vernetzer                  import vernetzer_analysieren, vernetzer_delta_aktualisieren
from agents.berichterstatter           import berichterstatter_erstellen
from agents.gespraechspartner          import gespraechspartner_starten
from agents.sekundaerquellen_analyst   import sekundaerquellen_analyst_starten

BUCHER_DIR       = r"E:\Bucher"
ANALYSEN_DIR     = r"E:\Claude_Projekte\Buchanalysen\analysen"
BIBLIOTHEK_INDEX = r"E:\Claude_Projekte\Buchanalysen\bibliothek\index.json"


def buecher_scannen() -> list[dict]:
    """Scannt E:\\Bucher\\ nach allen PDF-Dateien und gibt eine strukturierte Liste zurück."""
    buecher = []

    for eintrag in os.scandir(BUCHER_DIR):
        if eintrag.is_dir():
            # PDFs in Unterordnern (z.B. Michael_Luders/)
            autor = eintrag.name.replace("_", " ")
            for datei in os.scandir(eintrag.path):
                if datei.name.lower().endswith(".pdf"):
                    titel = os.path.splitext(datei.name)[0].replace("_", " ").replace("-", " ")
                    buecher.append({
                        "autor":       autor,
                        "autor_ordner": eintrag.name,
                        "titel":       titel,
                        "titel_ordner": os.path.splitext(datei.name)[0],
                        "pdf_pfad":    datei.path,
                    })
        elif eintrag.name.lower().endswith(".pdf"):
            # PDFs direkt im Hauptordner
            titel = os.path.splitext(eintrag.name)[0].replace("_", " ").replace("-", " ")
            buecher.append({
                "autor":        "Verschiedene",
                "autor_ordner": "Verschiedene",
                "titel":        titel,
                "titel_ordner": os.path.splitext(eintrag.name)[0],
                "pdf_pfad":     eintrag.path,
            })

    return sorted(buecher, key=lambda b: (b["autor"], b["titel"]))


def pfade_erstellen(buch: dict) -> dict:
    """Erstellt alle Ausgabepfade für ein Buch."""
    basis = os.path.join(ANALYSEN_DIR, buch["autor_ordner"], buch["titel_ordner"])
    return {
        "basis":        basis,
        "lektor":       os.path.join(basis, "01_lektor.md"),
        "analyse":      os.path.join(basis, "02_inhaltsanalyse.md"),
        "vernetzung":   os.path.join(basis, "03_vernetzung.md"),
        "bericht":      os.path.join(basis, "04_bericht.md"),
    }


def bereits_analysiert(pfade: dict) -> list[str]:
    """Prüft welche Analyseschritte bereits vorhanden sind."""
    vorhanden = []
    namen = ["lektor", "analyse", "vernetzung", "bericht"]
    dateien = ["01_lektor.md", "02_inhaltsanalyse.md", "03_vernetzung.md", "04_bericht.md"]
    for name, datei in zip(namen, dateien):
        if os.path.exists(pfade[name]):
            vorhanden.append(name)
    return vorhanden


def menu_anzeigen(buecher: list[dict]) -> None:
    """Zeigt das Buchauswahl-Menü."""
    print("\n" + "="*60)
    print("  BUCHANALYSE-SYSTEM")
    print("="*60)
    print(f"\n  Verfügbare Bücher in E:\\Bucher\\ ({len(buecher)} PDFs gefunden):\n")

    aktueller_autor = ""
    for i, buch in enumerate(buecher, start=1):
        if buch["autor"] != aktueller_autor:
            print(f"\n  [{buch['autor']}]")
            aktueller_autor = buch["autor"]
        print(f"    {i:2}. {buch['titel']}")

    print("\n" + "-"*60)


async def vernetzungen_aktualisieren(neuer_autor: str, neuer_titel: str) -> None:
    """Aktualisiert die Vernetzung aller anderen Bücher im Archiv (Delta-Modus).

    Für jedes bestehende Buch:
    - Haiku prüft ob eine Verbindung zum neuen Buch besteht
    - Sonnet schreibt nur wenn relevant einen neuen Abschnitt (kein Neuschreiben)
    """
    with open(BIBLIOTHEK_INDEX, "r", encoding="utf-8") as f:
        bibliothek = json.load(f)

    andere = [b for b in bibliothek["buecher"]
              if not (b["autor"] == neuer_autor and b["titel"] == neuer_titel)]

    if not andere:
        print("  Keine anderen Bücher im Archiv – Delta-Vernetzung nicht nötig.")
        return

    # Pfade des neuen Buches aus dem Index holen
    neuer_lektor_pfad = None
    neue_inhaltsanalyse_pfad = None
    for b in bibliothek["buecher"]:
        if b["autor"] == neuer_autor and b["titel"] == neuer_titel:
            neuer_lektor_pfad = b["lektor_pfad"]
            neue_inhaltsanalyse_pfad = b.get("inhaltsanalyse_pfad", "")
            break

    if not neuer_lektor_pfad:
        print("  [Fehler] Neues Buch nicht im Index gefunden – Delta-Vernetzung abgebrochen.")
        return

    print(f"\n{'='*60}")
    print(f"  DELTA-VERNETZUNG: {len(andere)} Bücher werden geprüft...")
    print(f"  (Haiku-Check → nur bei Verbindung wird Sonnet geschrieben)")
    print(f"{'='*60}")

    uebersprungen = 0
    ergaenzt = 0

    for i, buch in enumerate(andere, start=1):
        print(f"\n  [{i}/{len(andere)}] {buch['autor']} – {buch['titel']}")

        wurde_ergaenzt = await vernetzer_delta_aktualisieren(
            bestehendes_buch=buch,
            neuer_autor=neuer_autor,
            neuer_titel=neuer_titel,
            neuer_lektor_pfad=neuer_lektor_pfad,
            neue_inhaltsanalyse_pfad=neue_inhaltsanalyse_pfad,
        )
        if wurde_ergaenzt:
            ergaenzt += 1
        else:
            uebersprungen += 1

    print(f"\n{'='*60}")
    print(f"  DELTA-VERNETZUNG ABGESCHLOSSEN!")
    print(f"  Ergänzt: {ergaenzt} Bücher | Übersprungen: {uebersprungen} Bücher")
    print(f"{'='*60}\n")


async def buch_analysieren(buch: dict) -> None:
    """Führt alle 4 Agenten für ein Buch aus."""
    pfade = pfade_erstellen(buch)
    vorhanden = bereits_analysiert(pfade)

    print(f"\n{'='*60}")
    print(f"  STARTE ANALYSE: {buch['autor']} – {buch['titel']}")
    print(f"{'='*60}")

    # Bereits vorhandene Schritte anzeigen
    if vorhanden:
        print(f"\n  Bereits vorhanden: {', '.join(vorhanden)}")
        antwort = input("  Alles neu analysieren? (j/n): ").strip().lower()
        if antwort != "j":
            # Nur fehlende Schritte ausführen
            print("  Nur fehlende Schritte werden ausgeführt.\n")

    # Schritt 1: Lektor
    if "lektor" not in vorhanden or antwort_ist_ja(vorhanden):
        print("\n  [1/4] LEKTOR startet...")
        await lektor_analysieren(buch["pdf_pfad"], pfade["lektor"])
    else:
        print("\n  [1/4] Lektor – bereits vorhanden, wird übersprungen.")

    # Schritt 2: Inhaltsanalyst
    if "analyse" not in vorhanden or antwort_ist_ja(vorhanden):
        print("\n  [2/4] INHALTSANALYST startet...")
        await inhaltsanalyst_analysieren(pfade["lektor"], pfade["analyse"])
    else:
        print("\n  [2/4] Inhaltsanalyst – bereits vorhanden, wird übersprungen.")

    # Schritt 3: Vernetzer
    if "vernetzung" not in vorhanden or antwort_ist_ja(vorhanden):
        print("\n  [3/4] VERNETZER startet...")
        await vernetzer_analysieren(
            autor               = buch["autor"],
            titel               = buch["titel"],
            lektor_pfad         = pfade["lektor"],
            inhaltsanalyse_pfad = pfade["analyse"],
            ausgabe_pfad        = pfade["vernetzung"],
        )
    else:
        print("\n  [3/4] Vernetzer – bereits vorhanden, wird übersprungen.")

    # Schritt 4: Berichterstatter
    if "bericht" not in vorhanden or antwort_ist_ja(vorhanden):
        print("\n  [4/4] BERICHTERSTATTER startet...")
        await berichterstatter_erstellen(
            autor               = buch["autor"],
            titel               = buch["titel"],
            lektor_pfad         = pfade["lektor"],
            inhaltsanalyse_pfad = pfade["analyse"],
            vernetzung_pfad     = pfade["vernetzung"],
            ausgabe_pfad        = pfade["bericht"],
        )
    else:
        print("\n  [4/4] Berichterstatter – bereits vorhanden, wird übersprungen.")

    print(f"\n{'='*60}")
    print(f"  ANALYSE ABGESCHLOSSEN!")
    print(f"  Ergebnis: {pfade['basis']}")
    print(f"{'='*60}\n")

    # Vernetzung aller anderen Bücher aktualisieren
    await vernetzungen_aktualisieren(buch["autor"], buch["titel"])


# Hilfsvariable für Neuanalyse-Entscheidung
_neuanalyse = False

def antwort_ist_ja(vorhanden: list) -> bool:
    return _neuanalyse


async def main() -> None:
    global _neuanalyse

    # API-Key prüfen
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n  FEHLER: Kein API-Schlüssel gefunden!")
        print("  Bitte in .env eintragen: ANTHROPIC_API_KEY=dein_schluessel")
        return

    while True:
        # Hauptmenü
        print("\n" + "="*60)
        print("  BUCHANALYSE-SYSTEM – HAUPTMENÜ")
        print("="*60)
        print("\n  Was möchtest du tun?\n")
        print("    1.  Buch analysieren")
        print("    2.  Über Bücher diskutieren")
        print("    3.  Quellen erkunden (Sekundärquellen-Analyst)")
        print("    q.  Beenden")
        print()

        try:
            modus = input("  Auswahl: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Auf Wiedersehen, Honzele!")
            break

        if modus == "q":
            print("\n  Auf Wiedersehen, Honzele!\n")
            break

        # MODUS 2: Diskutieren
        elif modus == "2":
            await gespraechspartner_starten()

        # MODUS 3: Quellen erkunden
        elif modus == "3":
            await sekundaerquellen_analyst_starten()

        # MODUS 1: Buch analysieren
        elif modus == "1":
            buecher = buecher_scannen()
            menu_anzeigen(buecher)

            try:
                eingabe = input("\n  Nummer eingeben (oder 'q' für Hauptmenü): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\n  Auf Wiedersehen, Honzele!")
                break

            if eingabe.lower() == "q":
                continue

            if not eingabe.isdigit() or not (1 <= int(eingabe) <= len(buecher)):
                print(f"\n  Ungültige Eingabe. Bitte eine Zahl zwischen 1 und {len(buecher)} eingeben.")
                continue

            buch = buecher[int(eingabe) - 1]
            pfade = pfade_erstellen(buch)
            vorhanden = bereits_analysiert(pfade)

            if vorhanden:
                antwort = input(f"\n  '{buch['titel']}' wurde bereits analysiert ({', '.join(vorhanden)}).\n  Alles neu analysieren? (j/n): ").strip().lower()
                _neuanalyse = (antwort == "j")
            else:
                _neuanalyse = True

            await buch_analysieren(buch)

            # Wiki-Kurator startet automatisch
            import subprocess
            wiki_dir = r"E:\Claude_Projekte\Wiki_Honzele"
            nachricht = f"Kuratiere {buch['titel']} von {buch['autor']}"
            print(f"\n{'='*60}")
            print(f"  WIKI-KURATOR startet...")
            print(f"{'='*60}\n")
            subprocess.run(["claude", nachricht], cwd=wiki_dir)

        else:
            print("\n  Bitte 1, 2 oder q eingeben.")


if __name__ == "__main__":
    asyncio.run(main())
