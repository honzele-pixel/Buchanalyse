---
name: start-buchanalyse
description: Automatisiert die vollständige Buchanalyse (Schritte 1-5). Führt Lektor (lokal), Inhaltsanalyse, Vernetzung, ein detailliertes Dossier und eine lückenlose Quellenextraktion aus den letzten 50 Seiten durch.
---

# Start_Buchanalyse Workflow

Dieser Skill automatisiert die Kern-Pipeline der Buchanalyse. Er stellt sicher, dass alle Schritte in der richtigen Reihenfolge und nach den Qualitätsvorgaben (Honzele-Standard) ausgeführt werden.

## Verwendung

Rufe den Skill auf mit:
`Start_Buchanalyse [Autor] - [Titel] [Pfad zum PDF]`

## Die 5 Schritte der Analyse

### Schritt 1: Lektor (Lokal via Ollama)
Der erste Schritt erfolgt zwingend lokal, um Kosten zu sparen.
- **Ziel:** Erstellung der `01_lektor.md`.
- **Anweisung:** Nutze das Skript `agents/lektor.py`.
- **Wichtig:** Der Timeout für den Ollama-Aufruf muss auf mindestens 3600 Sekunden (1 Stunde) gesetzt werden, um Abbrüche bei großen Dateien zu verhindern.
- **Kein API-Guthaben verwenden.**

### Schritt 2: Inhaltsanalyse
Basiert auf der `01_lektor.md`.
- **Ziel:** Erstellung der `02_inhaltsanalyse.md`.
- **Fokus:** Präzise Analyse von These, Argumentation und Methodik.

### Schritt 3: Vernetzung
Setzt das Buch in Beziehung zum bestehenden Archiv.
- **Ziel:** Erstellung der `03_vernetzung.md`.
- **Basis:** `bibliothek/index.json` und die Berichte anderer Bücher.

### Schritt 4: Gesamtdossier (Bericht)
Verdichtet alle bisherigen Erkenntnisse in ein strukturiertes Dokument `04_bericht.md`.
- **Strukturvorgabe (Strikt einhalten):**
    1. **Steckbrief & Kernthesen:** Kompakte Übersicht.
    2. **Zentrale Argumentationsketten:** 3-4 konkrete, ausführlich beschriebene Beispiele oder Beweisführungen direkt aus dem Buch (für mehr inhaltliche Tiefe).
    3. **Das stärkste Argument des Buches:** Detaillierte Erläuterung.
    4. **Die wichtigsten Zitate:** 10-15 prägnante Aussagen mit Seitenangabe.
    5. **Einordnung & Archiv-Bedeutung:** Vernetzung mit dem Bestand.
- **Wichtig:** Keine subjektiven oder nicht im Buch belegbaren Bewertungskriterien in diesem Bericht verwenden.

### Schritt 5: Lückenlose Quellenextraktion
Sichert die Erfassung aller Quellen durch Fokus auf den Anhang.
- **Prozess:**
    1. Führe das Skript `scripts/extract_last_pages.py [Pfad zum PDF] 50` aus.
    2. Übergib den extrahierten Rohtext an das Modell.
    3. Erstelle `05_quellen.md` mit vollständiger Bibliografie, Endnoten und einer Prioritätsbewertung für die Sekundäranalyse.

## Verzeichnisstruktur
Die Analysen werden immer unter `analysen/[Autor]/[Buch]/` gespeichert.
Stelle sicher, dass am Ende des Workflows der `bibliothek/index.json` aktualisiert wird.
