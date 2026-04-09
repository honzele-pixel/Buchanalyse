# Buchanalysen – Projektanleitung für Claude

## Was ist dieses Projekt?

Spezialisierte Claude-Agenten die Bücher aus Honzeles PDF-Bibliothek (`E:\Bucher\`) analysieren.
Gleichzeitig ein Lernprojekt: Honzele baut hier sein Verständnis von Claude Code und KI-Agenten auf.

**WICHTIG:** Dieses Projekt hat NICHTS mit dem geplanten Website-Projekt "Archiv der Souveränität" zu tun!
Es ist ein eigenständiges, privates Buchanalyse-Werkzeug – ausschließlich für Honzeles persönlichen Gebrauch.
Keine Geheimarchiv-Sprache, keine Dossier-Ästhetik, keine Gamification-Elemente hier einfließen lassen.

## Arbeitsverzeichnis
`E:\Claude_Projekte\Buchanalysen\`

## PDF-Bibliothek
`E:\Bucher\` – mit Unterordnern: Michael_Luders, Daniele_Ganser, Hannah_Arendt, Ukraine, u.a.

## Fertige Agenten (Stand 05.04.2026)

| Agent | Datei | Aufgabe |
|---|---|---|
| 1 – Lektor | `agents/lektor.py` | PDF vollständig lesen, in Abschnitte aufteilen, strukturieren |
| 2 – Inhaltsanalyst | `agents/inhaltsanalyst.py` | Kernthesen, Argumentation, Methodik, blinde Flecken |
| 3 – Vernetzer | `agents/vernetzer.py` | Querverbindungen zur Bibliothek, Archiv-Index pflegen |
| 4 – Berichterstatter | `agents/berichterstatter.py` | Finales Gesamtdossier aus allen 3 Analysen |
| 5 – Gesprächspartner | `agents/gespraechspartner.py` | Interaktive Buchdiskussion auf Basis aller 4 Analysen |

## Starten
```
python main.py
```
- **Modus 1:** Buch analysieren – alle 4 Agenten laufen automatisch nacheinander durch, danach werden die Vernetzungen **aller anderen Bücher automatisch aktualisiert**
- **Modus 2:** Über ein Buch diskutieren – Buchauswahl, dann freies Gespräch
**Wichtig:** Immer nur ein Terminal, nie parallel – wegen bibliothek/index.json

## Analyse-Ausgabe
Jedes Buch bekommt einen eigenen Ordner unter `analysen/<Autor>/<Buchtitel>/`:
- `01_lektor.md` – Rohaufbereitung
- `02_inhaltsanalyse.md` – Tiefenanalyse
- `03_vernetzung.md` – Querverbindungen
- `04_bericht.md` – Finales Gesamtdossier

## Bereits analysierte Bücher
- Michael Lüders: Krieg ohne Ende (04.04.2026)
- Hannah Arendt: Die Freiheit frei zu sein (04.04.2026)
- Rainer Mausfeld: Hegemonie oder Untergang (04.04.2026)
- Daniele Ganser: Illegale Kriege (04.04.2026)
- Rainer Mausfeld: Warum schweigen die Lämmer? (05.04.2026)
- Rainer Mausfeld: Hybris und Nemesis (05.04.2026)

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

## Nächste Schritte
- [ ] Weitere Bücher analysieren (z.B. Honzeles Vorträge: Frieden_und_Krieg, Projekt Demokratie)
- [ ] Ab 6-8 Büchern: Agent 6 (Beobachter) bauen – wöchentliche Web-Suche zu Buchthemen ← JETZT MÖGLICH (6 Bücher im Archiv)
- [ ] Website-Projekt gestartet: `E:\Claude_Projekte\Buchanalyse_Webseite\`

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

## Zukunftsidee
Die Buchanalysen könnten später als Wissensbasis für den KI-Experten im
Forensik-Labor der Website "Archiv der Souveränität" dienen.
Status: Idee – erst wenn Website steht und Buchbasis gewachsen ist.
