---
name: buchanalyse-workflow
description: Verwenden, wenn es in diesem Buchanalysen-Repo um den gesamten Analyseablauf, die Reihenfolge der Agenten, Ausgabedateien, erneute Durchlaeufe oder Sicherheitsregeln rund um Index-Aktualisierungen und parallele Ausfuehrung geht.
---

# Buchanalyse-Workflow

Diesen Skill nur fuer das lokale Repo `E:\Claude_Projekte\Buchanalysen` verwenden.

## Zweck

Dieser Skill erklaert den bestehenden Ablauf des Projekts. Er aendert keinen Code.
Er ist ein kompakter Leitfaden, um die aktuelle Analyse-Pipeline sicher zu verstehen und damit zu arbeiten.

## Wann benutzen

Diesen Skill benutzen, wenn der Nutzer zum Beispiel fragt:

- Wie laeuft eine Buchanalyse in diesem Repo ab?
- Welche Datei entsteht zuerst, welche danach?
- Was passiert nach einer abgeschlossenen Buchanalyse automatisch?
- Kann ich zwei Analysen gleichzeitig starten?
- Wo sollte ich nachsehen, bevor ich `main.py` oder `agents/` aendere?

Diesen Skill nicht fuer allgemeine Python-Fragen benutzen, die nichts Spezielles mit diesem Repo zu tun haben.

## Ablauf

Einstieg:

- Projektstart mit `python main.py`

Hauptablauf fuer ein Buch:

1. Buch aus `E:\Bucher` auswaehlen
2. `agents/lektor.py` ausfuehren
   - **WICHTIG:** Alle Rohtext-Chunks (Chunks des PDF-Inhalts vor der Analyse) MÜSSEN im Unterordner `01_lektor_rohtext/` des Buchordners abgespeichert werden. Dieser extrahierte Text ist extrem wertvoll und muss vollständig verfügbar bleiben!
3. `02_inhaltsanalyse.md` erzeugen
4. `03_vernetzung.md` erzeugen
5. `04_bericht.md` erzeugen
6. `05_quellen.md` erzeugen
   - **WICHTIG:** Sollten in `01_lektor.md` keine Quellen oder nur unzureichende Angaben gefunden werden, muss zwingend ein Python-Script (`tools/seiten_extrahieren.py`) genutzt werden, um die letzten 50 Seiten des Buches als Rohtext zu extrahieren. Dieser Text ist dann die Grundlage für die manuelle oder KI-gestützte Extraktion in `05_quellen.md`.
7. Vernetzung anderer bereits analysierter Buecher im Delta-Modus aktualisieren

## Sicherheitsregeln

- **Daten-Integrität:** Lösche niemals die Rohtext-Chunks in `01_lektor_rohtext/`. Sie sind die "Blackbox" und Versicherung des Projekts.
- **Vollständigkeit der Quellen:** Akzeptiere niemals ein leeres `05_quellen.md`. Wenn die Lektor-Synthese versagt, nutze den 50-Seiten-Fallback.
- Niemals davon ausgehen, dass parallele Ausfuehrung in diesem Repo sicher ist.
- `bibliothek/index.json` als empfindlichen gemeinsamen Zustand behandeln.
- Vor Aenderungen am Ablauf immer `CLAUDE.md` lesen.
- Wenn Ausgabedateien schon existieren, pruefen, ob eine komplette Neuanalyse oder nur fehlende Schritte gewuenscht sind.
- Wenn der Nutzer einen Kostenstopp oder "kein API-Guthaben verbrauchen" vorgibt, ist das eine harte Regel und hat Vorrang vor bequemen Python-Starts der Agenten 2-4.

## Hinweise fuer Aenderungen

Vor Aenderungen am Workflow-Code diese Stellen pruefen:

- `main.py`
- `agents/`
- `CLAUDE.md`

Wenn der Ablauf erklaert wird:

- einfache Sprache benutzen
- die echte aktuelle Reihenfolge beschreiben
- klar trennen zwischen "so arbeitet der Code jetzt" und "das waeren moegliche spaetere Verbesserungen"

## Erwartete Antwortweise

Bei Antworten fuer Anfaenger in diesem Repo:

- den Ablauf Schritt fuer Schritt erklaeren
- die konkreten Dateinamen nennen
- deutlich vor paralleler Ausfuehrung warnen
- keine zusaetzliche Architektur einfuehren, wenn der Nutzer nicht danach fragt
