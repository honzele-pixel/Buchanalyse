"""
Buchanalyse-System - Hauptprogramm

Workflow (kostenoptimiert):
  1. Lektorieren (Ollama lokal, gratis) -> 01_lektor.md + index.json

  Danach in Claude Code:
    "Analysiere [Autor] - [Titel]"       -> 02_inhaltsanalyse.md (gratis, Abo)
    "Vernetze [Autor] - [Titel]"         -> 03_vernetzung.md    (gratis, Abo)
    "Erstelle Bericht [Autor] - [Titel]" -> 04_bericht.md       (gratis, Abo)

Verwendung: python main.py
"""

from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv

from agents.lektor import lektor_analysieren
from bibliothek.index_utils import buch_in_bibliothek_registrieren
from config import settings
from status_report import main as status_report_main

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

BUCHER_DIR = settings.BIBLIOTHEK_DIR
ANALYSEN_DIR = settings.ANALYSEN_DIR


_neuanalyse = False



def buecher_scannen() -> list[dict]:
    """Scannt E:\\Bucher\\ nach allen PDF-Dateien und gibt eine strukturierte Liste zurueck."""
    buecher = []

    for eintrag in os.scandir(BUCHER_DIR):
        if eintrag.is_dir():
            autor = eintrag.name.replace("_", " ")
            for datei in os.scandir(eintrag.path):
                if datei.name.lower().endswith((".pdf", ".epub")):
                    titel = os.path.splitext(datei.name)[0].replace("_", " ").replace("-", " ")
                    buecher.append(
                        {
                            "autor": autor,
                            "autor_ordner": eintrag.name,
                            "titel": titel,
                            "titel_ordner": os.path.splitext(datei.name)[0],
                            "pdf_pfad": datei.path,
                        }
                    )
        elif eintrag.name.lower().endswith((".pdf", ".epub")):
            titel = os.path.splitext(eintrag.name)[0].replace("_", " ").replace("-", " ")
            buecher.append(
                {
                    "autor": "Verschiedene",
                    "autor_ordner": "Verschiedene",
                    "titel": titel,
                    "titel_ordner": os.path.splitext(eintrag.name)[0],
                    "pdf_pfad": eintrag.path,
                }
            )

    return sorted(buecher, key=lambda b: (b["autor"], b["titel"]))


def pfade_erstellen(buch: dict) -> dict:
    """Erstellt alle Ausgabepfade fuer ein Buch."""
    basis = os.path.join(ANALYSEN_DIR, buch["autor_ordner"], buch["titel_ordner"])
    return {
        "basis": basis,
        "lektor": os.path.join(basis, "01_lektor.md"),
        "analyse": os.path.join(basis, "02_inhaltsanalyse.md"),
        "vernetzung": os.path.join(basis, "03_vernetzung.md"),
        "bericht": os.path.join(basis, "04_bericht.md"),
    }


def bereits_analysiert(pfade: dict) -> list[str]:
    """Prueft, welche Analyseschritte bereits vorhanden sind."""
    vorhanden = []
    for name in ("lektor", "analyse", "vernetzung", "bericht"):
        if os.path.exists(pfade[name]):
            vorhanden.append(name)
    return vorhanden


def menu_anzeigen(buecher: list[dict]) -> None:
    """Zeigt das Buchauswahl-Menue."""
    print("\n" + "=" * 60)
    print("  BUCHANALYSE-SYSTEM")
    print("=" * 60)
    print(f"\n  Verfuegbare Buecher in E:\\Bucher\\ ({len(buecher)} PDFs gefunden):\n")

    aktueller_autor = ""
    for i, buch in enumerate(buecher, start=1):
        if buch["autor"] != aktueller_autor:
            print(f"\n  [{buch['autor']}]")
            aktueller_autor = buch["autor"]
        print(f"    {i:2}. {buch['titel']}")

    print("\n" + "-" * 60)


def antwort_ist_ja() -> bool:
    return _neuanalyse


def neuanalyse_entscheidung_setzen(buch: dict, pfade: dict) -> None:
    global _neuanalyse

    vorhanden = bereits_analysiert(pfade)
    if vorhanden:
        antwort = input(
            f"\n  '{buch['titel']}' wurde bereits analysiert ({', '.join(vorhanden)}).\n"
            "  Alles neu analysieren? (j/n): "
        ).strip().lower()
        _neuanalyse = antwort == "j"
    else:
        _neuanalyse = True


def standard_hinweise_anzeigen() -> None:
    print("\n  Lektorierung erzeugt:")
    print("    - 01_lektor.md")
    print("    - Eintrag in bibliothek/index.json")
    print("\n  Danach in Claude Code:")
    print("    'Analysiere [Autor] - [Titel]'     -> 02_inhaltsanalyse.md")
    print("    'Vernetze [Autor] - [Titel]'        -> 03_vernetzung.md")
    print("    'Erstelle Bericht [Autor] - [Titel]' -> 04_bericht.md")



async def standardanalyse_ausfuehren(buch: dict) -> None:
    """Fuehrt die Lektorierung aus und registriert das Buch im Index."""
    pfade = pfade_erstellen(buch)
    vorhanden = bereits_analysiert(pfade)

    print(f"\n{'=' * 60}")
    print(f"  STARTE LEKTORIERUNG: {buch['autor']} - {buch['titel']}")
    print(f"{'=' * 60}")

    if vorhanden:
        print(f"\n  Bereits vorhanden: {', '.join(vorhanden)}")
        if not antwort_ist_ja():
            print("  Nur fehlende Schritte werden ausgefuehrt.\n")

    if "lektor" not in vorhanden or antwort_ist_ja():
        print("\n  [1/1] LEKTOR startet...")
        await lektor_analysieren(buch["pdf_pfad"], pfade["lektor"])
    else:
        print("\n  [1/1] Lektor - bereits vorhanden, wird uebersprungen.")

    print("\n  Index wird aktualisiert...")
    buch_in_bibliothek_registrieren(
        autor=buch["autor"],
        titel=buch["titel"],
        lektor_pfad=pfade["lektor"],
        analyse_pfad=pfade["analyse"],
    )

    print(f"\n{'=' * 60}")
    print("  LEKTORIERUNG ABGESCHLOSSEN!")
    print(f"  Ergebnis: {pfade['basis']}")
    print("\n  Weiter in Claude Code:")
    print(f"    'Analysiere {buch['autor']} - {buch['titel']}'")
    print(f"{'=' * 60}\n")




def buch_auswaehlen() -> dict | None:
    buecher = buecher_scannen()
    menu_anzeigen(buecher)

    try:
        eingabe = input("\n  Nummer eingeben (oder 'q' fuer Hauptmenue): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n\n  Auf Wiedersehen, Honzele!")
        return None

    if eingabe.lower() == "q":
        return None

    if not eingabe.isdigit() or not (1 <= int(eingabe) <= len(buecher)):
        print(f"\n  Ungueltige Eingabe. Bitte eine Zahl zwischen 1 und {len(buecher)} eingeben.")
        return None

    return buecher[int(eingabe) - 1]


async def main() -> None:
    global _neuanalyse

    while True:
        print("\n" + "=" * 60)
        print("  BUCHANALYSE-SYSTEM - HAUPTMENUE")
        print("=" * 60)
        print("\n  Was moechtest du tun?\n")
        print("    1.  Lektorieren (Lektor lokal, gratis)")
        print("        -> danach in Claude Code: Analysiere / Vernetze / Erstelle Bericht")
        print("    2.  Statusbericht / Arbeitsliste")
        print("    q.  Beenden")
        print()
        print("  In Claude Code (alle gratis, kein API-Billing):")
        print("    'Analysiere [Autor] - [Titel]'         -> 02_inhaltsanalyse.md")
        print("    'Vernetze [Autor] - [Titel]'           -> 03_vernetzung.md")
        print("    'Erstelle Bericht [Autor] - [Titel]'   -> 04_bericht.md")
        print("    'Extrahiere Quellen [Autor] - [Titel]' -> 05_quellen.md")
        print("    'Sekundaerquellen [Autor] - [Titel]'   -> Diskussion + 06_sekundaerquellen/")
        print("    'Diskutiere [Autor] - [Titel]'         -> Interaktive Diskussion")
        print()

        try:
            modus = input("  Auswahl: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Auf Wiedersehen, Honzele!")
            break

        if modus == "q":
            print("\n  Auf Wiedersehen, Honzele!\n")
            break

        if modus == "1":
            standard_hinweise_anzeigen()
            buch = buch_auswaehlen()
            if not buch:
                continue
            pfade = pfade_erstellen(buch)
            neuanalyse_entscheidung_setzen(buch, pfade)
            await standardanalyse_ausfuehren(buch)

        elif modus == "2":
            status_report_main([])

        else:
            print("\n  Bitte 1, 2, 3, 4, 5 oder q eingeben.")


if __name__ == "__main__":
    asyncio.run(main())
