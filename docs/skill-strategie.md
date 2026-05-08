# Skill-Strategie fuer Buchanalysen

Diese Datei legt fest, welche Skills fuer dieses Projekt wirklich relevant sind.
Ziel ist ein kleiner, klarer Satz an Hilfen statt einer unuebersichtlichen Gesamtmenge.

## Grundregel

- `Global` nur fuer allgemeine, projektuebergreifende Arbeit verwenden.
- `Lokal` nur fuer Regeln und Workflows dieses Buchanalyse-Repos verwenden.
- Andere installierte Skills gelten nicht automatisch als relevant fuer dieses Projekt.

## Global sinnvoll

Diese Skills sind auch in anderen Projekten nuetzlich und duerfen global installiert bleiben:

- `python-patterns`
- `python-testing`
- `verification-loop`
- `git-workflow`
- `codebase-onboarding` oder `repo-scan`
- optional: `documentation-lookup`

## Lokal fuer dieses Repo sinnvoll

Diese Themen gehoeren projektlokal beschrieben und nicht global verallgemeinert:

- Buchanalyse-Workflow von `main.py`
- Rollen der Agenten in `agents/`
- Dateikonventionen in `analysen/`
- Schutzregeln fuer `bibliothek/index.json`
- Reihenfolge der Ausgaben `01_lektor.md` bis `06_index.md`
- Regel: keine parallelen Durchlaeufe

## Fuer dieses Repo bewusst ignorieren

Die folgenden Skill-Arten sind fuer `Buchanalysen` in der Regel nicht relevant:

- Frontend-, Design- und Website-Skills
- Mobile-Skills wie Android, Flutter, Swift oder Kotlin
- Deployment-, Vercel- und CI/CD-lastige Skills
- Billing-, Finance-, Investor- und Social-Media-Skills
- Healthcare-, HIPAA- und Compliance-Spezialskills
- Video-, Marketing- und Content-Distribution-Skills
- Plugin-, MCP- oder Connector-Bau, solange dieses Repo nur lokal arbeitet

## Praktische Entscheidung

Wenn unklar ist, ob ein Skill benutzt werden soll, gilt fuer dieses Repo:

1. Erst pruefen, ob das Problem mit Python-, Test-, Git- oder Verifikationswissen loesbar ist.
2. Dann pruefen, ob die Regel projektspezifisch ist und deshalb lokal dokumentiert werden sollte.
3. Alles andere nur verwenden, wenn ein echter Bedarf im Repo nachweisbar ist.

## Erster lokaler Skill

Der erste bewusst kleine lokale Skill fuer dieses Repo liegt hier:

- `.codex/skills/buchanalyse-workflow/SKILL.md`

Er beschreibt nur den aktuellen Buchanalyse-Ablauf und die wichtigsten Schutzregeln.
