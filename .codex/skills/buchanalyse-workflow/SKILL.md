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
3. `02_inhaltsanalyse.md` erzeugen
4. `03_vernetzung.md` erzeugen
5. `04_bericht.md` erzeugen
6. Vernetzung anderer bereits analysierter Buecher im Delta-Modus aktualisieren

Wichtig zur Ausfuehrung von Schritt 3-5:

- Wenn kein API-Guthaben verbraucht werden darf, Schritt 3-5 nie ueber Python-Prozesse starten.
- In diesem Fall Schritt 3-5 nur direkt in Claude Code anhand der Prompt-Dateien unter `Prompt/` ausfuehren.
- Nur `agents/lektor.py` darf dann lokal ueber Ollama laufen.

Wichtiger Ausgabeordner:

- `analysen/<Autor>/<Buchtitel>/`

Wichtige Ausgabedateien:

- `01_lektor.md`
- `02_inhaltsanalyse.md`
- `03_vernetzung.md`
- `04_bericht.md`

Optionale spaetere Dateien bei manchen Buechern:

- `05_quellen.md`
- `06_index.md`

## Sicherheitsregeln

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
