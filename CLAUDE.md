# Buchanalysen – Projektanleitung für Claude

## Was ist dieses Projekt?

Spezialisierte Claude-Agenten die Bücher aus Honzeles PDF-Bibliothek (`E:\Bucher\`) analysieren.
Gleichzeitig ein Lernprojekt: Honzele baut hier sein Verständnis von Claude Code und KI-Agenten auf.

**WICHTIG:** Dieses Projekt hat NICHTS mit dem geplanten Website-Projekt "Archiv der Souveränität" zu tun!
Es ist ein eigenständiges, privates Buchanalyse-Werkzeug – ausschließlich für Honzeles persönlichen Gebrauch.
Keine Geheimarchiv-Sprache, keine Dossier-Ästhetik, keine Gamification-Elemente hier einfließen lassen.

## Arbeitsverzeichnis
`E:\Claude_Projekte\Buchanalysen\`

## Skill-Fokus fuer dieses Repo

Dieses Projekt nutzt nur einen kleinen, bewusst eingegrenzten Skill-Satz.

- Globale Skills nur fuer allgemeine Python-, Test-, Git- und Verifikationsarbeit
- Projektspezifische Regeln nur lokal fuer dieses Buchanalyse-Repo
- Andere installierte Skills nicht automatisch als relevant behandeln

Die verbindliche Einordnung steht in `docs/skill-strategie.md`.

## PDF-Bibliothek
`E:\Bucher\` – mit Unterordnern: Michael_Luders, Daniele_Ganser, Hannah_Arendt, Ukraine, u.a.

## Fertige Agenten (Stand 2026-05-09)

| Agent | Startweg | Aufgabe |
|---|---|---|
| 1 – Lektor | `python main.py` → Modus 1 | PDF vollständig lesen, in Abschnitte aufteilen, strukturieren |
| 2 – Inhaltsanalyst | Claude Code: *"Analysiere ..."* | Kernthesen, Argumentation, Methodik, blinde Flecken |
| 3 – Vernetzer | Claude Code: *"Vernetze ..."* | Querverbindungen zur Bibliothek, Archiv-Index pflegen |
| 4 – Berichterstatter | Claude Code: *"Erstelle Bericht ..."* | Finales Gesamtdossier aus allen 3 Analysen |
| 5 – Gesprächspartner | Claude Code: *"Diskutiere ..."* | Interaktive Buchdiskussion auf Basis aller Analysen |
| 6 – Quellenextraktor | Claude Code: *"Extrahiere Quellen ..."* | Quellen aus 01_lektor.md extrahieren + Prioritätsbewertung |
| 7 – Sekundärquellen-Analyst | Claude Code: *"Sekundärquellen ..."* | Index-gestützte Tiefenanalyse + Diskussion + Wiki-Injektion |

**Alle Python-Agenten ausser Lektor und Gesprächspartner wurden entfernt.**
Schritte 2–4 und 6–7 laufen nur noch über die Prompt-Dateien in `Prompt/`.
Fuer diese Schritte gibt es keinen Python-Startpfad mehr.

## Starten

### Empfohlener Workflow (kostenoptimiert – Stand 2026-05-08)

**Schritt 1: Lektorieren** (Ollama lokal, gratis)
```
python main.py   ← Modus 1: Lektorieren
```
→ erzeugt `01_lektor.md` + aktualisiert `bibliothek/index.json`

**Schritt 2–4: Analyse, Vernetzung, Bericht** (Claude Code Abo, gratis)

In Claude Code:
- *"Analysiere [Autor] – [Titel]"* → `02_inhaltsanalyse.md`
- *"Vernetze [Autor] – [Titel]"* → `03_vernetzung.md`
- *"Erstelle Bericht [Autor] – [Titel]"* → `04_bericht.md`
- *"Extrahiere Quellen [Autor] – [Titel]"* → `05_quellen.md`
- *"Sekundärquellen [Autor] – [Titel]"* → Diskussion + `06_sekundaerquellen/`
- *"Diskutiere [Autor] – [Titel]"* → Interaktive Diskussion + optionaler Abschlussbericht

System-Prompts:
- `Prompt/System_Prompt_Inhaltsanalyst.md`
- `Prompt/System_Prompt_Vernetzer.md`
- `Prompt/System_Prompt_Berichterstatter.md`
- `Prompt/System_Prompt_Quellenextraktor.md`
- `Prompt/System_Prompt_Sekundaerquellen_Analyst.md`
- `Prompt/System_Prompt_Gespraechspartner.md`

**Warum:** Alle Schritte ausser dem Lektor lesen nur vorhandene Markdown-Dateien und
schreiben neue – das kann Claude Code direkt, ohne API-Billing.
Nur der Lektor braucht Python (PyMuPDF + Ollama lokal).

**Wichtig:** Immer nur ein Terminal, nie parallel – wegen `bibliothek/index.json`

**Kostenregel:** Alle Schritte ausser Lektor (Modus 1) laufen ausschliesslich über
Claude Code. Es gibt dafuer keinen Python-Startpfad mehr.

## Analyse-Ausgabe
Jedes Buch bekommt einen eigenen Ordner unter `analysen/<Autor>/<Buchtitel>/`:
- `01_lektor.md` – Rohaufbereitung
- `02_inhaltsanalyse.md` – Tiefenanalyse
- `03_vernetzung.md` – Querverbindungen
- `04_bericht.md` – Finales Gesamtdossier
- `05_quellen.md` – Extrahierte Quellen + Prioritätsbewertung
- `06_sekundaerquellen/06_index.md` – Prioritätsliste für Sekundäranalysen
- `06_sekundaerquellen/06_*.md` – Einzelne Sekundärquellen-Tiefenanalysen

## Bereits analysierte Bücher
- Michael Lüders: Krieg ohne Ende (04.04.2026)
- Hannah Arendt: Die Freiheit frei zu sein (04.04.2026)
- Rainer Mausfeld: Hegemonie oder Untergang (04.04.2026)
- Daniele Ganser: Illegale Kriege (04.04.2026)
- Rainer Mausfeld: Warum schweigen die Lämmer? (05.04.2026)
- Rainer Mausfeld: Hybris und Nemesis (05.04.2026)
- Michael Lüders: Drecksarbeit (10.04.2026)
- Immanuel Kant: Grundlegung zur Metaphysik der Sitten (11.04.2026)
- Immanuel Kant: Zum ewigen Frieden (12.04.2026)
- Verheugen/Erler: Der lange Weg zum Krieg (12.04.2026)
- Jeffrey Sachs: Diplomatie oder Desaster (27.04.2026)

## Technische Basis
- `claude-agent-sdk` installiert
- Python + dotenv vorhanden
- API-Schlüssel in `.env`
- Git-Versionskontrolle aktiv
- **Wichtig:** System-Prompt wird via `SystemPromptFile` als Datei übergeben (nicht als Argument) – notwendig wegen Windows-Limit für Befehlszeilen-Argumente
- **Wichtig:** Lektor-Synthese verwendet direkte `anthropic`-API (nicht SDK) – claude CLI bricht bei langen Streaming-Antworten auf Windows ab
- **Wichtig:** Lektor speichert Chunks sofort in `.chunk_cache/` – bei Abbruch werden fertige Chunks beim nächsten Start wiederverwendet (kein Doppelzahlen)

## KRITISCHE REGELN (aus gescheiterten Vorprojekten gelernt)

1. **Immer zuerst zeigen, dann bestätigen, dann umsetzen** – nie eigenständig Änderungen vornehmen
2. **Git von Tag 1** – jeder Schritt wird versioniert
3. **Schritt für Schritt** – mit dem Einfachsten beginnen
4. **Honzele ist Anfänger** – jeden Schritt verständlich erklären, keine Programmierkenntnisse voraussetzen
5. **Kein Bezug zur Website "Archiv der Souveränität"** – das sind zwei völlig separate Projekte
6. **NIEMALS "fertig" oder "Test bestanden" sagen ohne vollständige Verifikation** – beim Buchanalyse-System bedeutet das: Agenten durchgelaufen UND generator.py der Webseite erfolgreich ausgeführt UND neues Buch korrekt sichtbar. Erst dann gilt ein Test als bestanden.

## Nächste Schritte
- [ ] Weitere Bücher analysieren (z.B. Honzeles Vorträge: Frieden_und_Krieg, Projekt Demokratie)
- [ ] Agent 6 in main.py als Modus 3 einbinden (derzeit nur direkt startbar)
- [ ] 06_index.md für Mausfeld: Hybris & Nemesis erstellen (556 Quellen, noch kein Index)
- [ ] 05_quellen.md + 06_index.md für restliche Bücher nachziehen (Lüders, Arendt, Kant, Ganser)
- [ ] Nächste ★★★★★-Sekundärquelle: Reich (1933/1971) – Massenpsychologie des Faschismus
- [x] Agent 6 (Sekundärquellen-Analyst) fertig – index-gestützt, Diskussion + Wiki-Injektion (27.04.2026)
- [x] Website-Projekt gestartet: `E:\Claude_Projekte\Buchanalyse_Webseite\`

## Modell-Strategie (geplant – verschoben auf später)

Aktuell: `settings.py` definiert `claude-opus-4-6` global, aber Lektor-Synthese nutzt hardcodiert `claude-sonnet-4-6` (direkte API). → Inkonsistenz, die beim nächsten Umbau bereinigt werden soll.

**Geplante Zuweisung je Agent:**

| Agent | Modell | Begründung |
|---|---|---|
| Lektor | Ollama lokal (gratis) | Nur Text strukturieren – kein tiefes Denken nötig |
| Inhaltsanalyst | Claude Opus | Herzstück der Analyse – hier lohnt das Stärkste |
| Vernetzer | Claude Haiku | Verbindungen finden – einfachere Aufgabe |
| Berichterstatter | Claude Sonnet | Strukturiertes Schreiben – Sonnet reicht vollständig |
| Gesprächspartner | Claude Opus | Interaktiv, unvorhersehbar – braucht das Stärkste |

- Honzele hat Ollama + Docker + OpenWebUI bereits installiert – Grundlage ist vorhanden
- Geschätzte Ersparnis: 50–70% ohne spürbaren Qualitätsverlust

## Automatische Vernetzung (Kernmerkmal)
Nach jeder neuen Buchanalyse werden die Vernetzungen **aller** bereits analysierten Bücher automatisch neu erstellt. Das Wissensnetz wächst mit jedem Buch vollständig – keine manuelle Nacharbeit nötig.

- **Delta-Vernetzer (Usage-Optimierung):** Um API-Kosten zu sparen und Zeitlimits zu umgehen, nutzt das System einen inkrementellen Workflow:
  1. **Haiku 4.5 (Relevanz-Check):** Prüft blitzschnell, ob das neue Buch für ein bestehendes Buch überhaupt relevant ist (Stärke 0-3).
  2. **Sonnet 4.6 (Delta-Content):** Nur bei Relevanz (Stärke > 0) schreibt Sonnet einen gezielten neuen Abschnitt und hängt ihn an die bestehende `03_vernetzung.md` an.
  3. **Vorteil:** Skaliert linear statt quadratisch (bei 50 Büchern: ~20 Min statt ~2 Std).
- Der Vernetzer schreibt strukturierte Verbindungen automatisch in `bibliothek/querverbindungen.json`
- Der Generator der Webseite liest Knoten und Verbindungen dynamisch aus den JSON-Dateien
- Kein manueller Eingriff in `generator.py` mehr nötig bei neuen Büchern

## GitHub
- Buchanalysen: https://github.com/honzele-pixel/Buchanalyse.git (Branch: master)
- Buchanalyse_Webseite: noch kein GitHub-Remote (nur lokal)

## Zukunftsidee: Themenmappe-Modus (geplant)
Erweiterung des Systems für Honzeles Nachdenkseiten-Sammlung (`E:\Nachdenkseiten\`):
- ~25 Themenordner mit PDFs (Israel, Ukraine, Iran, NATO, China, Jacques Baud, Ulrike Guerot u.a.)
- **Idee:** Lektor liest alle PDFs eines Ordners → Gesprächspartner diskutiert die ganze Themenmappe
- Vereinfachter Workflow ohne Inhaltsanalyst/Vernetzer/Berichterstatter (schneller, günstiger)
- Offene Fragen: Ordner = Themenmappe? Einzelartikel oder gebündelt? Wo landen die Ergebnisse?
- Status: Geplant – beim nächsten Gespräch angehen

## Zukunftsidee: Website-Verbindung
Die Buchanalysen könnten später als Wissensbasis für den KI-Experten im
Forensik-Labor der Website "Archiv der Souveränität" dienen.
Status: Idee – erst wenn Website steht und Buchbasis gewachsen ist.
