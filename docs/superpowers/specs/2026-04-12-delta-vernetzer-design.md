# Design: Intelligenter Delta-Vernetzer

**Datum:** 2026-04-12  
**Projekt:** Buchanalysen – E:\Claude_Projekte\Buchanalysen  
**Ziel:** Vernetzungs-Updates skalieren mit der Bibliothek – ohne Qualitätsverlust

---

## Problem

Wenn ein neues Buch analysiert wird, laufen für alle N anderen Bücher komplette
Vernetzer-Durchläufe. Das ist O(N) vollständige API-Aufrufe mit wachsenden Prompts.
Bei 50 Büchern: ~2 Stunden und hohe API-Kosten. Der Großteil ist unnötig, weil sich
die Verbindungen A↔B, A↔C nicht verändert haben – nur A↔X ist neu.

---

## Lösung: Delta-Vernetzer

### Kernprinzip

- **Neues Buch X** → voller Vernetzer (unverändert, liest alle anderen Bücher)
- **Bestehende Bücher A, B, C...** → Delta-Vernetzer (nur Buch A + Buch X)

### Ablauf

```
Buch X (neu)
  └─→ vernetzer_analysieren() [unverändert] → 03_vernetzung.md ✓

Für jedes bestehende Buch A, B, C...:
  └─→ [1] Haiku: Relevanz-Check
        ├─ Stärke 0 → überspringen
        └─ Stärke 1–3 → [2] Sonnet: Delta-Abschnitt schreiben
                            → an 03_vernetzung.md anhängen
                            → querverbindungen.json aktualisieren
```

### Phase 1 – Relevanz-Check (Haiku)

**Input:** Kurzbeschreibung Buch A + Kurzbeschreibung Buch X (je max. 2.000 Zeichen)  
**Output:** JSON `{ "staerke": 0–3, "themen": ["..."] }`  
**Schwellenwert:** Stärke ≥ 1 → Delta-Abschnitt wird geschrieben  
**Modell:** claude-haiku-4-5-20251001

### Phase 2 – Delta-Abschnitt (Sonnet)

**Input:** Volles Profil Buch A (lektor + inhaltsanalyse, je max. 8.000 Zeichen) + volles Profil Buch X  
**Output:** Markdown-Abschnitt mit:
- Thematische Querverbindungen
- Argumentative Brücken
- Empfohlene Lesekombination

**Format im 03_vernetzung.md:**
```markdown
---

## Neue Verbindung: [Autor X] – [Titel X] (ergänzt YYYY-MM-DD)

[Inhalt des Delta-Abschnitts]
```

**Modell:** claude-sonnet-4-6

### querverbindungen.json

Neue Verbindungen A↔X werden eingetragen (bestehende Verbindungen A↔B, A↔C bleiben unberührt).
Alte A↔X Einträge werden vor dem Schreiben entfernt um Duplikate zu vermeiden.

---

## Änderungen am Code

### Neue Funktion in `agents/vernetzer.py`

```python
async def vernetzer_delta_aktualisieren(
    bestehendes_buch: dict,   # aus bibliothek/index.json
    neuer_autor: str,
    neuer_titel: str,
    neuer_lektor_pfad: str,
    neue_inhaltsanalyse_pfad: str,
) -> None
```

### Geänderte Funktion in `main.py`

`vernetzungen_aktualisieren()` ruft statt `vernetzer_analysieren()` die neue
`vernetzer_delta_aktualisieren()` auf.

### Kein Umbau bestehender Logik

- `vernetzer_analysieren()` bleibt vollständig unverändert
- Das neue Buch X durchläuft weiterhin den vollen Vernetzer
- Nur die Aktualisierung der bestehenden Bücher wird optimiert

---

## Qualitätssicherung

**Kernprinzip:** Die Qualität darf nicht sinken.

- Sonnet (nicht Haiku) schreibt die inhaltlichen Abschnitte
- Der Haiku-Check entscheidet nur ob → nicht was geschrieben wird
- Der neue Abschnitt folgt demselben Struktur-Schema wie der bestehende Vernetzungstext
- Das Datum der Ergänzung ist sichtbar → Transparenz über Entstehungsgeschichte

---

## Geschwindigkeit (Hochrechnung)

| Bücher | Vorher | Nachher |
|--------|--------|---------|
| 10     | ~15 Min | ~5 Min |
| 20     | ~30 Min | ~8 Min |
| 50     | ~2 Std  | ~20 Min |
| 100    | ~5 Std  | ~40 Min |

---

## Nicht im Scope

- Vollständige Neu-Vernetzung aller Bücher (bleibt manuell auslösbar)
- Umbau des Lektor- oder Inhaltsanalysten
- Modell-Strategie-Umbau (verschoben laut CLAUDE.md)
