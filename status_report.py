r"""
Lokaler Statusbericht fuer das Buchanalyse-Projekt.

Prueft:
- PDFs in E:\Bucher
- Analyse-Dateien in analysen/
- Registrierung in bibliothek/index.json

Keine API-Aufrufe. Nur lokale Dateipruefung.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict


PROJEKT_DIR = os.path.dirname(os.path.abspath(__file__))
BUCHER_DIR = r"E:\Bucher"
ANALYSEN_DIR = os.path.join(PROJEKT_DIR, "analysen")
INDEX_PFAD = os.path.join(PROJEKT_DIR, "bibliothek", "index.json")

STUFEN = {
    "01": "01_lektor.md",
    "02": "02_inhaltsanalyse.md",
    "03": "03_vernetzung.md",
    "04": "04_bericht.md",
    "05": "05_quellen.md",
    "06": os.path.join("06_sekundaerquellen", "06_index.md"),
}

STATUS_REIHENFOLGE = [
    "ANALYSIERT",
    "INDEX OFFEN",
    "QUELLEN OFFEN",
    "INDEX FEHLT",
    "IN ARBEIT",
    "NEU",
]


def slug_text(text: str) -> str:
    return text.replace("_", " ").replace("-", " ").strip()


def normalize_text(text: str) -> str:
    return (
        text.lower()
        .replace("ä", "a")
        .replace("ö", "o")
        .replace("ü", "u")
        .replace("ß", "ss")
        .replace("_", " ")
        .replace("-", " ")
        .strip()
    )


def scan_buecher() -> list[dict]:
    buecher: list[dict] = []

    for eintrag in os.scandir(BUCHER_DIR):
        if eintrag.is_dir():
            autor = slug_text(eintrag.name)
            for datei in os.scandir(eintrag.path):
                if datei.is_file() and datei.name.lower().endswith(".pdf"):
                    titel_ordner = os.path.splitext(datei.name)[0]
                    buecher.append(
                        {
                            "autor": autor,
                            "autor_ordner": eintrag.name,
                            "titel": slug_text(titel_ordner),
                            "titel_ordner": titel_ordner,
                            "pdf_pfad": datei.path,
                        }
                    )
        elif eintrag.is_file() and eintrag.name.lower().endswith(".pdf"):
            titel_ordner = os.path.splitext(eintrag.name)[0]
            buecher.append(
                {
                    "autor": "Verschiedene",
                    "autor_ordner": "Verschiedene",
                    "titel": slug_text(titel_ordner),
                    "titel_ordner": titel_ordner,
                    "pdf_pfad": eintrag.path,
                }
            )

    return sorted(buecher, key=lambda buch: (buch["autor"], buch["titel"]))


def analyse_basis(buch: dict) -> str:
    return os.path.join(ANALYSEN_DIR, buch["autor_ordner"], buch["titel_ordner"])


def lade_index() -> dict:
    if not os.path.exists(INDEX_PFAD):
        return {"buecher": []}

    with open(INDEX_PFAD, "r", encoding="utf-8") as handle:
        return json.load(handle)


def index_maps(index_daten: dict) -> tuple[dict[tuple[str, str], dict], dict[str, dict]]:
    nach_name: dict[tuple[str, str], dict] = {}
    nach_basis: dict[str, dict] = {}

    for eintrag in index_daten.get("buecher", []):
        autor = normalize_text(eintrag.get("autor", ""))
        titel = normalize_text(eintrag.get("titel", ""))
        nach_name[(autor, titel)] = eintrag

        lektor_pfad = eintrag.get("lektor_pfad", "")
        if lektor_pfad:
            basis = os.path.dirname(lektor_pfad)
            nach_basis[os.path.normcase(basis)] = eintrag

    return nach_name, nach_basis


def datei_status(basis: str) -> dict[str, bool]:
    status: dict[str, bool] = {}
    for nummer, dateiname in STUFEN.items():
        status[nummer] = os.path.exists(os.path.join(basis, dateiname))
    return status


def klassifiziere_buch(dateien: dict[str, bool], im_index: bool) -> str:
    hat_01_bis_04 = all(dateien[stufe] for stufe in ("01", "02", "03", "04"))
    hat_irgendwas = any(dateien.values())

    if not hat_irgendwas:
        return "NEU"
    if hat_01_bis_04 and not dateien["05"]:
        return "QUELLEN OFFEN"
    if hat_01_bis_04 and dateien["05"] and not dateien["06"]:
        return "INDEX OFFEN"
    if hat_01_bis_04 and not im_index:
        return "INDEX FEHLT"
    if hat_01_bis_04:
        return "ANALYSIERT"
    return "IN ARBEIT"


def naechster_schritt(status: str, dateien: dict[str, bool], im_index: bool) -> str:
    if status == "NEU":
        return "Modus 1: Buch analysieren"
    if status == "IN ARBEIT":
        for stufe in ("01", "02", "03", "04"):
            if not dateien[stufe]:
                return f"Fehlende Hauptstufe {stufe} erzeugen"
        return "Teilstatus pruefen"
    if status == "INDEX FEHLT" or not im_index:
        return "Vernetzer/Index pruefen"
    if status == "QUELLEN OFFEN":
        return "Modus 4: 05_quellen.md erzeugen"
    if status == "INDEX OFFEN":
        return "Modus 3: 06_index.md erzeugen"
    return "Kein Handlungsbedarf"


def pruefe_index_eintrag(eintrag: dict) -> list[str]:
    fehler: list[str] = []

    lektor_pfad = eintrag.get("lektor_pfad", "")
    analyse_pfad = eintrag.get("inhaltsanalyse_pfad", "")

    if not lektor_pfad or not os.path.exists(lektor_pfad):
        fehler.append("lektor_pfad fehlt oder existiert nicht")
    if analyse_pfad and not os.path.exists(analyse_pfad):
        fehler.append("inhaltsanalyse_pfad existiert nicht")

    return fehler


def format_stufen(dateien: dict[str, bool]) -> str:
    teile = []
    for nummer in ("01", "02", "03", "04", "05", "06"):
        teile.append(f"{nummer}:{'OK' if dateien[nummer] else '--'}")
    return " ".join(teile)


def scan_analyse_ordner() -> list[str]:
    gefundene: list[str] = []
    if not os.path.exists(ANALYSEN_DIR):
        return gefundene

    for root, _, files in os.walk(ANALYSEN_DIR):
        if "01_lektor.md" in files:
            gefundene.append(os.path.normcase(root))
    return sorted(set(gefundene))


def collect_report_data() -> dict:
    buecher = scan_buecher()
    index_daten = lade_index()
    index_nach_name, index_nach_basis = index_maps(index_daten)

    eintraege = []
    zaehler: Counter[str] = Counter()
    handlungs_zaehler: Counter[str] = Counter()
    index_fehler_gesamt = 0
    gefundene_index_keys: set[int] = set()
    bekannte_basen: set[str] = set()

    for buch in buecher:
        basis = analyse_basis(buch)
        bekannte_basen.add(os.path.normcase(basis))
        dateien = datei_status(basis)
        norm_key = (normalize_text(buch["autor"]), normalize_text(buch["titel"]))
        index_eintrag = index_nach_basis.get(os.path.normcase(basis))
        if index_eintrag is None:
            index_eintrag = index_nach_name.get(norm_key)

        im_index = index_eintrag is not None
        status = klassifiziere_buch(dateien, im_index)
        aktion = naechster_schritt(status, dateien, im_index)
        fehler: list[str] = []

        if index_eintrag is not None:
            gefundene_index_keys.add(id(index_eintrag))
            fehler = pruefe_index_eintrag(index_eintrag)
            index_fehler_gesamt += len(fehler)

        eintrag = {
            "autor": buch["autor"],
            "titel": buch["titel"],
            "autor_ordner": buch["autor_ordner"],
            "titel_ordner": buch["titel_ordner"],
            "pdf_pfad": buch["pdf_pfad"],
            "analyse_basis": basis,
            "im_index": im_index,
            "status": status,
            "naechster_schritt": aktion,
            "dateien": dateien,
            "index_fehler": fehler,
        }
        eintraege.append(eintrag)
        zaehler[status] += 1
        handlungs_zaehler[aktion] += 1

    index_only = []
    for eintrag in index_daten.get("buecher", []):
        if id(eintrag) not in gefundene_index_keys:
            index_only.append(eintrag)

    analyse_only = []
    for basis in scan_analyse_ordner():
        if basis not in bekannte_basen:
            analyse_only.append(basis)

    return {
        "meta": {
            "projekt_dir": PROJEKT_DIR,
            "buecher_dir": BUCHER_DIR,
            "index_pfad": INDEX_PFAD,
        },
        "eintraege": eintraege,
        "summary": {
            "gesamt_pdfs": len(buecher),
            "index_eintraege": len(index_daten.get("buecher", [])),
            "index_fehler_gesamt": index_fehler_gesamt,
            "status_counts": dict(zaehler),
            "aktions_counts": dict(handlungs_zaehler),
        },
        "index_only": index_only,
        "analyse_only": analyse_only,
    }


def filter_entries(
    eintraege: list[dict],
    *,
    only_open: bool = False,
    status_filter: str | None = None,
    author_filter: str | None = None,
) -> list[dict]:
    status_filter_norm = status_filter.upper() if status_filter else None
    author_filter_norm = author_filter.lower() if author_filter else None

    gefiltert = []
    for eintrag in eintraege:
        if only_open and eintrag["status"] == "ANALYSIERT":
            continue
        if status_filter_norm and eintrag["status"] != status_filter_norm:
            continue
        if author_filter_norm and author_filter_norm not in eintrag["autor"].lower():
            continue
        gefiltert.append(eintrag)
    return gefiltert


def drucke_textbericht(report: dict, eintraege: list[dict], only_open: bool) -> None:
    meta = report["meta"]
    summary = report["summary"]

    print("=" * 100)
    print("STATUS REPORT - BUCHANALYSEN")
    print("=" * 100)
    print(f"Projekt: {meta['projekt_dir']}")
    print(f"Buecher : {meta['buecher_dir']}")
    print(f"Index   : {meta['index_pfad']}")
    if only_open:
        print("Filter  : nur offene Buecher")
    print()

    for eintrag in eintraege:
        marker = "IDX" if eintrag["im_index"] else "---"
        print(f"[{eintrag['status']:<14}] [{marker}] {eintrag['autor']} - {eintrag['titel']}")
        print(f"  {format_stufen(eintrag['dateien'])}")
        print(f"  Naechster Schritt: {eintrag['naechster_schritt']}")
        for meldung in eintrag["index_fehler"]:
            print(f"  INDEX-FEHLER: {meldung}")
        print()

    if report["index_only"]:
        print("=" * 100)
        print("INDEX-EINTRAEGE OHNE PASSENDES PDF")
        print("=" * 100)
        for eintrag in report["index_only"]:
            print(f"- {eintrag.get('autor', '?')} - {eintrag.get('titel', '?')}")
        print()

    if report["analyse_only"]:
        print("=" * 100)
        print("ANALYSE-ORDNER OHNE PASSENDES PDF")
        print("=" * 100)
        for basis in report["analyse_only"]:
            print(f"- {basis}")
        print()

    print("=" * 100)
    print("PRIORISIERTE ARBEITSLISTE")
    print("=" * 100)
    gruppen: dict[str, list[str]] = defaultdict(list)
    for eintrag in eintraege:
        if eintrag["status"] == "ANALYSIERT":
            continue
        gruppen[eintrag["naechster_schritt"]].append(f"{eintrag['autor']} - {eintrag['titel']}")

    if not gruppen:
        print("Keine offenen Schritte.")
    else:
        sortierung = [
            "Modus 4: 05_quellen.md erzeugen",
            "Modus 3: 06_index.md erzeugen",
            "Vernetzer/Index pruefen",
            "Fehlende Hauptstufe 01 erzeugen",
            "Fehlende Hauptstufe 02 erzeugen",
            "Fehlende Hauptstufe 03 erzeugen",
            "Fehlende Hauptstufe 04 erzeugen",
            "Modus 1: Buch analysieren",
            "Teilstatus pruefen",
        ]
        for aktion in sortierung:
            if aktion not in gruppen:
                continue
            print(f"- {aktion}: {len(gruppen[aktion])}")
            for name in gruppen[aktion]:
                print(f"  {name}")
    print()

    print("=" * 100)
    print("ZUSAMMENFASSUNG")
    print("=" * 100)
    print(f"Gesamtzahl PDFs       : {summary['gesamt_pdfs']}")
    print(f"Index-Eintraege       : {summary['index_eintraege']}")
    print(f"Index-Fehler gesamt   : {summary['index_fehler_gesamt']}")
    for status in STATUS_REIHENFOLGE:
        print(f"{status:<20}: {summary['status_counts'].get(status, 0)}")


def baue_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Statusbericht fuer das Buchanalyse-Projekt")
    parser.add_argument("--only-open", action="store_true", help="Nur Buecher mit offenem Arbeitsstand anzeigen")
    parser.add_argument("--status", help="Nur einen Status anzeigen, z.B. 'INDEX OFFEN'")
    parser.add_argument("--author", help="Nur Buecher eines Autors anzeigen (Teilstring)")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Ausgabeformat")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = baue_parser()
    args = parser.parse_args(argv)

    report = collect_report_data()
    eintraege = filter_entries(
        report["eintraege"],
        only_open=args.only_open,
        status_filter=args.status,
        author_filter=args.author,
    )

    if args.format == "json":
        output = {
            "meta": report["meta"],
            "summary": report["summary"],
            "index_only": report["index_only"],
            "analyse_only": report["analyse_only"],
            "eintraege": eintraege,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0

    drucke_textbericht(report, eintraege, args.only_open)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
