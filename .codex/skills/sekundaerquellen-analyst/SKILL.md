---
name: sekundaerquellen-analyst
description: Tiefgehende Analyse von Sekundärquellen (Literaturverzeichnis) auf Doktoranden-Niveau. Inklusive epistemischer Prüfung, Diskurskartierung und Wiki-Injektion. Use when the user asks for "Sekundärquellen [Autor] - [Titel]" or "Quellenanalyse [Buchtitel]".
---

# Sekundärquellen-Analyst

Dieser Skill automatisiert die Tiefenanalyse von Sekundärliteratur, die in den analysierten Büchern zitiert wird. Er hilft dabei, die wissenschaftliche Basis des Primärwerks zu prüfen und Querverbindungen zum restlichen Archiv sowie zum Wiki herzustellen.

## Modi

### 1. Diskussionsmodus
Vorschlag von 2-3 Quellen für die nächste Tiefenanalyse basierend auf Priorität und Wissenslücken.
**Trigger:** `Sekundaerquellen [Autor] - [Titel]` oder `Quellenanalyse [Buchtitel]`.

### 2. Analysemodus (Tiefenanalyse)
Erstellung einer detaillierten `06_*.md` Datei nach explizitem Auftrag.
**Trigger:** `Erstelle Analyse [Quelle]` oder `B [Quelle]`.

## Arbeitsweise

1. **Kontext laden:** Lade den Quellen-Index (`05_quellen.md`), die Inhaltsanalyse (`02_inhaltsanalyse.md`) und den Bericht (`04_bericht.md`) des Primärwerks.
2. **Referenz beachten:** Nutze `analysen/Rainer_Mausfeld/Hegemonie_oder_Untergang/06_sekundaerquellen/06_mirowski_2015.md` als qualitativen Goldstandard.
3. **Struktur einhalten:** Analysen folgen einer strikten Struktur von bibliografischer Identifikation bis hin zum Wiki-Potenzial (siehe `references/prompt.md`).
4. **Wiki-Integration:** Identifiziere Begriffe für das Wiki und schlage neue Seiten vor.

## Verzeichnisstruktur
- **Index:** `analysen/[Autor]/[Buch]/06_sekundaerquellen/06_index.md`
- **Einzelanalysen:** `analysen/[Autor]/[Buch]/06_sekundaerquellen/06_[autor]_[jahr].md`

Detaillierte Anweisungen und das Ausgabeformat findest du in `references/prompt.md`.
