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

## Fertige Agenten (Stand 04.04.2026)

| Agent | Datei | Aufgabe |
|---|---|---|
| 1 – Lektor | `agents/lektor.py` | PDF vollständig lesen, in Abschnitte aufteilen, strukturieren |
| 2 – Inhaltsanalyst | `agents/inhaltsanalyst.py` | Kernthesen, Argumentation, Methodik, blinde Flecken |
| 3 – Vernetzer | `agents/vernetzer.py` | Querverbindungen zur Bibliothek, Archiv-Index pflegen |
| 4 – Berichterstatter | `agents/berichterstatter.py` | Finales Gesamtdossier aus allen 3 Analysen |

## Analyse-Ausgabe
Jedes Buch bekommt einen eigenen Ordner unter `analysen/<Autor>/<Buchtitel>/`:
- `01_lektor.md` – Rohaufbereitung
- `02_inhaltsanalyse.md` – Tiefenanalyse
- `03_vernetzung.md` – Querverbindungen
- `04_bericht.md` – Finales Gesamtdossier

## Bereits analysierte Bücher
- Michael Lüders: Krieg ohne Ende (04.04.2026)

## Technische Basis
- `claude-agent-sdk` installiert
- Python + dotenv vorhanden
- API-Schlüssel in `.env`
- Git-Versionskontrolle aktiv

## KRITISCHE REGELN (aus gescheiterten Vorprojekten gelernt)

1. **Immer zuerst zeigen, dann bestätigen, dann umsetzen** – nie eigenständig Änderungen vornehmen
2. **Git von Tag 1** – jeder Schritt wird versioniert
3. **Schritt für Schritt** – mit dem Einfachsten beginnen
4. **Honzele ist Anfänger** – jeden Schritt verständlich erklären, keine Programmierkenntnisse voraussetzen
5. **Kein Bezug zur Website "Archiv der Souveränität"** – das sind zwei völlig separate Projekte

## Nächste Schritte
- [ ] `main.py` – zentraler Einstiegspunkt mit Buchauswahl-Menü (alle 4 Agenten automatisch nacheinander)
- [ ] Nächstes Buch analysieren (Empfehlung Vernetzer: Mausfeld – Warum schweigen die Lämmer?)
- [ ] Agent 5: Beobachter – wöchentliche Web-Suche zu Buchthemen (geplant)

## Zukunftsidee
Die Buchanalysen könnten später als Wissensbasis für den KI-Experten im
Forensik-Labor der Website "Archiv der Souveränität" dienen.
Status: Idee – erst wenn Website steht und Buchbasis gewachsen ist.
