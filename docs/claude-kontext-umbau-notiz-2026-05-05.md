# Claude-Kontext-Umbau: Sitzungsnotiz vom 2026-05-05

## Ziel

Die Claude-Konfiguration soll deutlich schlanker, thematisch sauberer und besser wartbar werden.

## Kern-Erkenntnisse

- Die globale `CLAUDE.md` ist zu breit und vermischt globale Regeln, persönliche Biografie, Tool-Notizen und projektspezifische Vorgaben.
- Die globale `CLAUDE.md` soll auf universelle Regeln reduziert werden.
- Persönliche Hintergründe, Tooling-Hinweise und thematische Speziallogik sollen in Referenzdateien ausgelagert werden.
- Projektspezifische Vorgaben gehören in das jeweilige lokale `CLAUDE.md` des Projekts, nicht in die globale Datei.

## Zielbild fuer die globale Struktur

- Schlanke globale `CLAUDE.md` mit nur universellen Regeln
- Referenzdatei `references/honzele-profil.md`
- Referenzdatei `references/tooling-notizen.md`
- Optional weitere thematische Referenzdateien statt globaler Ueberladung

## Inhalt der kuenftigen globalen `CLAUDE.md`

- Antworten standardmaessig auf Deutsch
- Nutzer mit `Honzele` ansprechen
- Klar, direkt und verstaendlich schreiben
- Fachbegriffe nur wenn noetig und dann kurz erklaeren
- Dateien vor Aenderungen lesen
- Keine inhaltlichen Entscheidungen anstelle von Honzele treffen
- Keine pauschalen Erfolgsaussagen ohne echte Verifikation
- Bei Codeprojekten nachvollziehbar und bevorzugt mit Git arbeiten

## Korrigierte Referenzpunkte

- Der aktiv genutzte Obsidian-Vault liegt im `Wiki Honzele`.
- Der Obsidian-Vault `Geopolitik_und_Krieg` wird ausdruecklich nicht verwendet.
- Bevorzugte Arbeitsumgebung ist `Claude Code`.
- Wenn das Session-Limit von Claude erreicht ist, koennen auch `Gemini` und `Codex` genutzt werden.

## Wichtige Fachentscheidung fuer kuenftige Geopolitik-Projekte

- Bei geopolitischen Gespraechen soll die KI nicht beliebig aus allgemeinem Modellwissen antworten.
- Stattdessen soll sie primaer auf kuratierte Wissensbestaende zugreifen:
  - `Wiki Honzele`
  - `Buchanalysen`
- Fuer einzelne Themen sollen spaeter gezielte Referenz-Zuordnungen gepflegt werden.

## Geplante Themenlogik

- Thema `Israel` -> bevorzugt auf passende Arbeiten von Michael Lueders stuetzen
- Thema `Ukraine` -> bevorzugt auf passende Buchanalysen stuetzen, zusaetzlich `Daniele Ganser: Illegale Kriege`
- Weitere geopolitische Themen -> ueber eigenes Themen-Routing mit priorisierten Referenzen abbilden

## Stilentscheidung fuer Geopolitik

- Antworten zu geopolitischen Themen sollen ruhig, sachlich, praezise und analytisch formuliert sein.
- Gewuenscht ist eine Vortragsweise, die Inhalte sauber herausarbeitet und nicht polemisch zuspitzt.
- Als Orientierung dient die als stark empfundene Vortragsart von Gabriele Krone-Schmalz.
- Das soll als Stilprofil beschrieben werden, nicht als starre Imitation.

## Architekturentscheidung

- Global = Verhaltensrahmen
- Referenzdateien = Hintergrundwissen
- Projektlokales `CLAUDE.md` = fachliche Steuerung fuer das konkrete Projekt

## Naechster Umbau in der naechsten Sitzung

1. Globale `CLAUDE.md` neu und schlank aufsetzen
2. Zwei globale Referenzdateien anlegen:
   - `references/honzele-profil.md`
   - `references/tooling-notizen.md`
3. Entscheidung treffen, ob geopolitische Spezialregeln global als Referenz oder in ein eigenes Projekt ausgelagert werden
4. Wahrscheinlich neues Projekt `Geopolitik` anlegen mit:
   - eigenem `CLAUDE.md`
   - `references/geopolitik-regeln.md`
   - `references/themen-routing.md`
   - `references/stilprofil.md`
5. Themen-Routing fuer Israel, Ukraine und weitere Felder konkret definieren

## Hinweis fuer den Wiedereinstieg

Wenn die Arbeit fortgesetzt wird, zuerst diese Datei lesen und dann den Umbau direkt entlang der Punkte unter `Naechster Umbau in der naechsten Sitzung` umsetzen.
