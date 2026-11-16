# AlgorithmusProjekt – wissenschaftliche Recherche für KI-Assistenten

Eine **RAG-Recherchepipeline** für wissenschaftliche Veröffentlichungen auf [arXiv](https://arxiv.org/), umgesetzt als Python-Projekt mit einem [MCP](https://modelcontextprotocol.io/)-Tool für KI-Assistenten wie Claude.

Entstanden als Gruppenprojekt (Gruppe 2) im FOM-Modul **Algorithmen \& Datenstrukturen**.

Das Tool lädt zu einer Suchanfrage bis zu 20 von arXiv bereits vorsortierte wissenschaftliche Arbeiten, bewertet deren Titel und Abstracts nochmals algorithmisch und gibt standardmäßig die 5 passendsten Textabschnitte mit Quellen an einen KI-Assistenten zurück.

## Inhaltsverzeichnis

* [Wofür ist das gut?](#wofür-ist-das-gut)
* [Konkretes Beispiel](#konkretes-beispiel)
* [Was passiert technisch?](#was-passiert-technisch)
* [Wie wird Relevanz berechnet?](#wie-wird-relevanz-berechnet)
* [Mehrwert und Grenzen](#mehrwert-und-grenzen)
* [Projektstatus](#projektstatus)
* [Voraussetzungen](#voraussetzungen)
* [Installation](#installation)
* [Benutzung](#benutzung)
* [PostgreSQL und Cache](#postgresql-und-cache)
* [Tests und Evaluation](#tests-und-evaluation)
* [Projektstruktur](#projektstruktur)
* [Fehlerbehebung](#fehlerbehebung)
* [Sicherheit und Lizenz](#sicherheit-und-lizenz)

## Wofür ist das gut?

KI-Assistenten können wissenschaftliche Fragen beantworten, müssen dafür aber geeignete Quellen finden und deren Inhalte verarbeiten. Dieses Projekt **übernimmt einen Teil der Quellenauswahl**, bevor ein Sprachmodell die Antwort formuliert.

Der Ansatz heißt **Retrieval-Augmented Generation (RAG)**: Ein externes System beschafft geeignete Informationen; das Sprachmodell erhält diese als Kontext und formuliert daraus eine Antwort.

Die angestrebten Vorteile sind:

* **Weniger Kontext für das Sprachmodell:** Statt bis zu 20 Titel/Abstracts erhält es standardmäßig 5 ausgewählte Abschnitte.
* **Nachvollziehbare Quellen:** Jeder Treffer enthält unter anderem Paper-ID, Titel, Autoren, Datum und arXiv-Link.
* **Reproduzierbare Vorauswahl:** Die Ranking-Algorithmen treffen die Auswahl anhand definierter Regeln und nicht allein durch das Sprachmodell.
* **Wiederverwendbare Ergebnisse:** PostgreSQL kann Suchergebnisse und bereits berechnete Textvektoren zwischenspeichern.

**Wichtig:** Ob das bei einer echten KI-Recherche insgesamt Tokens, Zeit oder Kosten spart und ob die Antworten dadurch korrekter werden, muss im Vergleich mit einer Recherche ohne Tool gemessen werden. Diese Vorteile sind **Projektziele, keine bereits nachgewiesenen Ergebnisse**.

## Konkretes Beispiel

**Frage an einen KI-Assistenten:**

> Welche Ansätze gibt es zur Fehlerkorrektur in Quantencomputern?

Ein MCP-fähiger Assistent kann dafür das Tool `research\_papers` aufrufen, beispielsweise mit:

```json
{
  "keywords": \["quantum error correction", "logical qubits"],
  "question": "Welche Ansätze gibt es zur Fehlerkorrektur in Quantencomputern?",
  "k": 5
}
```

Dann passiert Folgendes:

1. Das Tool fragt die **arXiv-API** nach den englischen Fachbegriffen. arXiv verknüpft sie mit **OR**, sortiert selbst nach Relevanz und liefert standardmäßig **maximal 20 Paper**.
2. Das Projekt entnimmt die **Titel und Abstracts**, nicht die vollständigen PDFs.
3. Es zerlegt die Texte gegebenenfalls in kleinere Abschnitte und bewertet diese mit einer **Keyword-Suche (BM25)**. Ist ein Voyage-API-Schlüssel eingerichtet, erfolgt zusätzlich eine **semantische Vektorsuche**.
4. Im hybriden Modus werden die Rankings kombiniert und sehr ähnliche Abschnitte bei der Endauswahl benachteiligt.
5. Der Assistent erhält die **5 ausgewählten Abschnitte als JSON** und kann damit seine Antwort samt Quellen formulieren.

Das Tool **schreibt die wissenschaftliche Antwort nicht selbst**. Es liefert die Textgrundlage. Der KI-Assistent ist weiterhin für die inhaltliche Einordnung verantwortlich.

Das Ergebnis enthält `hits` und `warnings`. Jeder Eintrag in `hits` führt unter anderem `document\_id`, `title`, `authors`, `published`, `url`, `text`, `chunk\_position` und `score`. Meldungen in `warnings` weisen beispielsweise auf einen Cache-Treffer oder den Rückfall auf reine Keyword-Suche hin.

## Was passiert technisch?

```text
Nutzerfrage
    │
    ▼
KI-Assistent ruft research\_papers(keywords, question, k, ...) auf
    │
    ▼
PostgreSQL-Suchcache prüfen (falls erreichbar)
    │
    ├── Treffer im Cache ───────────────────────────────┐
    │                                                    │
    └── Kein Treffer: arXiv-API, bis zu 20 Paper ───────┤
                                                         ▼
                                                Titel + Abstracts
                                                         │
                                                         ▼
                                           Chunks bis 200 Wörter
                                            (40 Wörter Überlappung)
                                                         │
                                                         ▼
                                              BM25-Keyword-Ranking
                                                         │
                                  ┌──────────────────────┴─────────────┐
                                  │                                    │
                           Ohne Voyage-Key                       Mit Voyage-Key
                                  │                                    │
                             Top-k nach BM25               Bis zu 50 BM25-Kandidaten
                                  │                                    │
                                  │                            Vektoren + Ähnlichkeit
                                  │                                    │
                                  │                             RRF-Rangfusion
                                  │                                    │
                                  │                          MMR: Relevanz + Vielfalt
                                  │                                    │
                                  └─────────────────┬──────────────────┘
                                                    ▼
                                          k Treffer mit Quellen
                                                    │
                                                    ▼
                                           KI formuliert Antwort
```

### Standardparameter

Die Werte stehen in [`src/pipeline/pipeline.py`](src/pipeline/pipeline.py):

|Parameter|Standard|Bedeutung|
|-|-:|-|
|`max\_documents`|`20`|Maximale Anzahl berücksichtigter arXiv-Paper|
|`chunk\_size`|`200`|Maximale Wörter pro Textabschnitt|
|`overlap`|`40`|Wörter, die sich benachbarte Abschnitte teilen|
|`candidates\_m`|`50`|Maximal durch BM25 vorselektierte Abschnitte|
|`k\_rrf`|`60`|Parameter zur Kombination der Rankings|
|`mmr\_lambda`|`0.7`|Gewichtung: Relevanz (70 %) gegenüber Unähnlichkeit (30 %)|
|`k`|`5`|Zurückgegebene Abschnitte; über MCP zulässig: `1` bis `20`|

Beim Filter `peer\_reviewed\_only=true` fragt die arXiv-Anbindung bei Bedarf bis zu dreimal so viele Treffer ab, filtert danach aber wieder auf maximal `max\_documents`.

## Wie wird Relevanz berechnet?

**1. arXiv trifft bereits die erste Auswahl.** Die Suche verwendet die übergebenen Keywords (`OR`-Verknüpfung) und `sortBy=relevance`. Die Pipeline sieht normalerweise nur die ersten 20 arXiv-Treffer. Ein fachlich passendes Paper außerhalb dieser Auswahl kann später nicht mehr gefunden werden.

**2. BM25 bewertet die Wörter.** Der Algorithmus berücksichtigt, ob und wie oft die Suchbegriffe in einem Abschnitt vorkommen, wie lang der Abschnitt ist und wie selten die Begriffe unter den **gerade geladenen Abschnitten** sind. Daraus entsteht ein Keyword-Relevanzwert. Ein invertierter Index beschleunigt das Nachschlagen; ein Heap ermittelt die besten Kandidaten.

**3. Optional: Voyage AI bewertet die inhaltliche Ähnlichkeit.** Die ursprüngliche Frage (oder ersatzweise die Keywords) und die Kandidaten werden über das Embedding-Modell `voyage-4` in Vektoren umgewandelt. Per **Cosine Similarity** werden semantisch ähnliche Texte höher bewertet, auch wenn ihre Wörter nicht exakt übereinstimmen.

**4. RRF verbindet die beiden Ranglisten.** Bei der *Reciprocal Rank Fusion* zählt die Platzierung eines Textabschnitts in der BM25- und der Vektorrangliste. Damit werden unterschiedlich skalierte Scores kombiniert.

**5. MMR sorgt für weniger Redundanz.** *Maximal Marginal Relevance* bevorzugt relevante Abschnitte, die sich nicht zu stark mit bereits ausgewählten Abschnitten überschneiden. Das verhindert nicht garantiert inhaltliche Duplikate, kann aber die Vielfalt verbessern.

**Wichtig für die Einordnung:** Ohne `VOYAGE\_API\_KEY` läuft **nur BM25**. RRF und MMR werden dann nicht verwendet. Findet BM25 gar keinen passenden Chunk, kann die hybride Suche ersatzweise alle geladenen Chunks semantisch prüfen. Außerdem führt die Begrenzung auf 20 Abstracts häufig dazu, dass BM25 mit `candidates\_m=50` nur wenige Kandidaten tatsächlich ausschließt.

## Mehrwert und Grenzen

|Was das Projekt heute tatsächlich macht|Was es nicht automatisch leistet|
|-|-|
|arXiv-Ergebnisse einheitlich aufbereiten|Keine eigenständige Suche über alle arXiv-Paper|
|Titel/Abstracts nach BM25 und optional Vektoren neu sortieren|Keine Analyse von Methoden, Tabellen oder Ergebnissen im Paper-Volltext|
|Wenige Textabschnitte mit Quellen an einen Assistenten liefern|Keine wissenschaftliche Prüfung der Richtigkeit der Inhalte|
|Wiederholte Suchen und Embeddings bei verfügbarer Datenbank zwischenspeichern|Keine Garantie für geringeren Tokenverbrauch oder kürzere Gesamtlaufzeit|
|Eine reproduzierbare Testbasis für Rankingverfahren bereitstellen|Keine Garantie, dass zitierte Aussagen durch die Quelle wirklich belegt sind|

Ein wichtiger methodischer Nachteil ist, dass BM25 seine Wortseltenheit (**IDF**) aus den **bereits durch arXiv vorgefilterten Treffern** berechnet. Gerade das Hauptkeyword kommt dort fast überall vor und kann dadurch wenig zur Unterscheidung beitragen. Details stehen in [`Phase5/Reflexion.md`](Phase5/Reflexion.md).

**Geeigneter Einsatz:** Demonstration und Evaluation von Such-, Ranking- und RAG-Verfahren sowie als experimentelles Recherchetool für Fragen, deren Antwort sich in Titel oder Abstract abzeichnet.

**Weniger geeigneter Einsatz:** Gezielte Fragen nach Messwerten, Tabellen, Versuchsmethoden oder Einschränkungen, die erst im Volltext eines Papers stehen. Dafür müsste die Volltextverarbeitung ergänzt werden.

## Projektstatus

Stand der Projektdokumentation: **15. November 2026**.

* Implementiert: arXiv-Anbindung, Chunking, BM25, Voyage-Vektorsuche, RRF, MMR, Pipeline und MCP-Server.
* Implementiert: PostgreSQL-Schema mit sechs Tabellen, Suchcache (7 Tage) und Wiederverwendung bekannter Embeddings.
* Dokumentiert: **325 Unittests** und **97 % Gesamtabdeckung** gemäß [`Phase4/Testdokumentation.md`](Phase4/Testdokumentation.md). Dies sind die dokumentierten Werte, keine hier erneut ausgeführten Tests.
* Vorbereitet: Skript für vergleichende Messläufe (`agent\_websearch`, `bm25`, `hybrid`). Die eigentliche KPI-Auswertung ist laut README/Reflexion noch offen.
* Offen: Recherche in Paper-Volltexten, bessere IDF-Grundlage, Bewertung über weitere Metadaten und belastbare Aussage zum praktischen Nutzen.

Aktuelle Aufgaben: [GitHub Issues](https://github.com/luca-1893/AlgorithmusProjekt/issues) · [Milestones](https://github.com/luca-1893/AlgorithmusProjekt/milestones).

## Voraussetzungen

|Programm / Dienst|Erforderlich?|Wofür?|
|-|-|-|
|**Git**|Für das Klonen empfohlen|Repository herunterladen und aktualisieren|
|**Python 3.15**|Ja|Projekt ausführen|
|**pip** und virtuelle Umgebung (`venv`)|Ja|Python-Abhängigkeiten isoliert installieren|
|**Internetverbindung zu arXiv**|Für echte neue Suchen|Wissenschaftliche Arbeiten abrufen|
|**PostgreSQL 18**|Optional für normale Suche; benötigt für Cache und DB-/Evaluationsläufe|Suche, Chunks, Vektoren und Messläufe speichern|
|**Voyage-AI-API-Key**|Optional|Semantische Suche; ohne Key nur BM25|
|**Claude Code / Claude Desktop oder anderer MCP-Client**|Für die Nutzung durch einen KI-Assistenten|`research\_papers` aufrufen|
|**Anthropic-API-Key**|Nur für echte Evaluation|Claude-Messläufe ausführen; kostenpflichtige API-Aufrufe|
|**Jupyter Notebook**|Für den Prototyp optional|Interaktive Demonstration; über `requirements.txt` installiert|

Die Python-Pakete (`anthropic`, `fastmcp`, `jupyter`, `psycopg`) stehen mit Versionen in [`requirements.txt`](requirements.txt), `coverage` für die Entwicklung in [`requirements-dev.txt`](requirements-dev.txt). Für Voyage werden HTTP-Anfragen direkt aus Python gestellt; ein separates Voyage-SDK ist nicht erforderlich.

## Installation

Die folgenden Befehle werden im **Projektverzeichnis** ausgeführt.

### 1\. Repository klonen

```bash
git clone https://github.com/luca-1893/AlgorithmusProjekt.git
cd AlgorithmusProjekt
```

### 2\. Virtuelle Umgebung anlegen und Abhängigkeiten installieren

**macOS (Homebrew) / Linux:**

```bash
# macOS: Python bei Bedarf installieren
brew install python@3.15

python3.15 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
export PYTHONPATH=src
```

Unter Linux Python 3.15 über einen geeigneten Paketmanager bzw. eine vorhandene Installation bereitstellen; `brew install` ist ein macOS-Beispiel.

**Windows (PowerShell; Python 3.15 muss installiert sein):**

```powershell
py -3.15 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
$env:PYTHONPATH = "src"
```

Falls PowerShell die Aktivierung der virtuellen Umgebung verhindert, die Python-Executable direkt über `.\\.venv\\Scripts\\python.exe` ausführen oder die Ausführungsrichtlinie für die aktuelle Sitzung prüfen.

### 3\. Optional: Voyage für die hybride Suche aktivieren

macOS/Linux (im aktuellen Terminal):

```bash
export VOYAGE\_API\_KEY="DEIN\_VOYAGE\_API\_KEY"
```

Windows PowerShell (im aktuellen Terminal):

```powershell
$env:VOYAGE\_API\_KEY = "DEIN\_VOYAGE\_API\_KEY"
```

Den eigenen Schlüssel einsetzen und **nicht committen**. Ohne Schlüssel bleibt die reine BM25-Suche nutzbar. Für die Evaluation mit Claude wird zusätzlich `ANTHROPIC\_API\_KEY` als Umgebungsvariable benötigt.

### 4\. Optional: Datenbank für Cache und Messläufe einrichten

Siehe [PostgreSQL und Cache](#postgresql-und-cache). Für den einfachen Suchtest ohne Cache ist das nicht nötig.

## Benutzung

### A. Direkter Suchtest ohne MCP-Client

Nach Aktivierung der Umgebung und Setzen von `PYTHONPATH`:

```bash
python -c 'import json; from pipeline import research; from sources import ArxivSource; print(json.dumps(research(\["quantum error correction"], 5, ArxivSource()).to\_dict(), ensure\_ascii=False, indent=2))'
```

Dieser Aufruf recherchiert live bei arXiv und nutzt **nur BM25**. Er benötigt weder PostgreSQL noch einen API-Key. Er ist ein funktionaler Suchtest, ersetzt aber keinen automatisierten Unittest.

### B. Mit Claude Code / einem MCP-Client

Der MCP-Server stellt genau ein Tool zur Verfügung:

```python
research\_papers(
    keywords: list\[str],
    k: int = 5,
    question: str = "",
    published\_after: str = "",
    peer\_reviewed\_only: bool = False,
)
```

* `keywords`: Englische Fachbegriffe für arXiv (empfohlen: 2 bis 8); die Liste wird per OR verknüpft.
* `k`: Anzahl der zurückgegebenen Textabschnitte, `1` bis `20` (Standard `5`).
* `question`: Originalfrage; verbessert im hybriden Modus die semantische Rangfolge.
* `published\_after`: Frühestes Veröffentlichungsdatum, `YYYY` oder `YYYY-MM-DD`.
* `peer\_reviewed\_only`: Filtert auf arXiv-Einträge mit DOI oder Journal-Referenz. **Das ist lediglich ein Indikator, kein Nachweis eines Peer-Reviews.**

**Claude Code:** Das Repository enthält bereits [`.mcp.json`](.mcp.json) mit einem Eintrag `recherche`. Bei Nutzung aus dem Projektverzeichnis kann Claude Code den lokalen Server starten; die Konfiguration verwendet standardmäßig `.venv/bin/python` und `PYTHONPATH=src`. Ein gesetzter `VOYAGE\_API\_KEY` wird an den Server weitergereicht. Für Windows den Interpreterpfad in `.mcp.json` auf `.venv\\\\Scripts\\\\python.exe` anpassen.

**MCP-Server manuell starten (macOS/Linux):**

```bash
PYTHONPATH=src .venv/bin/python -m mcp\_server
```

**MCP-Server manuell starten (Windows PowerShell):**

```powershell
$env:PYTHONPATH = "src"
.\\.venv\\Scripts\\python.exe -m mcp\_server
```

Der Standardtransport ist **stdio**. Dabei erscheint keine Weboberfläche; der gestartete Prozess kommuniziert mit dem MCP-Client über Ein-/Ausgabe.

Für einen lokalen HTTP-MCP-Endpunkt:

```bash
PYTHONPATH=src .venv/bin/python -m mcp\_server --transport http --host 127.0.0.1 --port 8000
```

Der MCP-Endpunkt liegt unter `/mcp`. Der HTTP-Server besitzt **keine eigene Authentifizierung**; nicht ungeschützt ins Internet stellen.

### C. Prototyp im Notebook ansehen

```bash
jupyter notebook Phase3/Prototyp.ipynb
```

Das Notebook zeigt die einzelnen Algorithmen, die Pipeline und beispielhafte Ausgaben sowie Fehlerfälle.

## PostgreSQL und Cache

Die Standardverbindung ist `postgresql:///algorithmusprojekt`, sofern `DATABASE\_URL` nicht gesetzt ist. Die lokale Datenbank muss existieren und der verwendete Datenbankbenutzer Zugriffsrechte besitzen.

**Beispiel für macOS mit Homebrew:**

```bash
brew install postgresql@18
brew services start postgresql@18

"$(brew --prefix postgresql@18)/bin/createdb" algorithmusprojekt
"$(brew --prefix postgresql@18)/bin/createdb" algorithmusprojekt\_test

"$(brew --prefix postgresql@18)/bin/psql" -d algorithmusprojekt -f sql/schema.sql
"$(brew --prefix postgresql@18)/bin/psql" -d algorithmusprojekt\_test -f sql/schema.sql
```

**Linux/Windows:** PostgreSQL 18 installieren, den Server starten und die Datenbanken `algorithmusprojekt` und `algorithmusprojekt\_test` anlegen. Mit `psql` das Schema aus `sql/schema.sql` in beide Datenbanken einspielen. Falls PostgreSQL nicht in `PATH` liegt, die vollständigen Pfade verwenden.

Die Tabellen sind:

|Tabelle|Inhalt|
|-|-|
|`documents`|arXiv-Paper und Metadaten; Schema ist für Volltexte vorbereitet|
|`chunks`|Textabschnitte der Dokumente|
|`chunk\_embeddings`|Gespeicherte Vektoren pro Text/Modell|
|`searches`|Suchanfragen und Zeitpunkte|
|`search\_documents`|Zuordnung der Ergebnisse zu den Suchanfragen|
|`runs`|Vergleichsmessungen zu Laufzeit, Tokens und Quellenfund|

**Cache-Verhalten:** Identische Suchen können **7 Tage** wiederverwendet werden; bekannte Textvektoren werden bei gleichem Text und Modell nicht erneut angefordert. Die PostgreSQL-Datenbank ist **kein vorab aufgebauter Volltextindex aller arXiv-Paper**, sondern speichert die im Betrieb abgerufenen Daten. Ist die Datenbank nicht erreichbar, wird die normale Suche ohne Cache fortgesetzt und das Ergebnis erhält einen Hinweis.

## Tests und Evaluation

### Automatisierte Tests

Aus dem Projektverzeichnis (mit aktivierter Umgebung):

```bash
python -m unittest discover -s src -t src
```

Coverage für Zeilen und Verzweigungen:

```bash
python -m coverage run --branch --source=src -m unittest discover -s src -t src
python -m coverage report --omit='\*/test\_\*.py,\*/\_\_init\_\_.py' -m
```

Für Datenbanktests muss die Testdatenbank `algorithmusprojekt\_test` mit dem Schema vorhanden und erreichbar sein. Die Testfälle und dokumentierten Resultate finden sich in [`Phase4/Testdokumentation.md`](Phase4/Testdokumentation.md) und [`Phase4/Testkatalog.md`](Phase4/Testkatalog.md).

### Vergleichsmessungen: Bringt das Tool wirklich etwas?

Die Evaluation vergleicht dieselben 25 Fragen in drei Varianten:

|Variante|Was Claude nutzt|
|-|-|
|`agent\_websearch`|Eigene Websuche ohne `research\_papers`|
|`bm25`|`research\_papers` mit reiner Keyword-Suche|
|`hybrid`|`research\_papers` mit BM25, Voyage-Vektorsuche, RRF und MMR|

Das Skript protokolliert unter anderem **Input-Tokens**, **Output-Tokens**, **Laufzeit** und, ob die **erwartete arXiv-ID** in der Antwort vorkommt (`found\_source`). Letzteres misst **nicht** direkt, ob alle Aussagen sachlich korrekt sind.

Für echte Messungen sind `ANTHROPIC\_API\_KEY`, für `hybrid` zusätzlich `VOYAGE\_API\_KEY`, sowie eine eingerichtete PostgreSQL-Datenbank nötig. API-Aufrufe können Kosten verursachen. Das im Code vorbelegte Claude-Modell lässt sich mit `--modell` überschreiben.

```bash
# Offline-Probe ohne Claude-/arXiv-Aufrufe; schreibt dennoch in PostgreSQL
python -m evaluation.messlauf --probe --fragen F01,F14

# Echter Test einer Frage mit reiner BM25-Suche
python -m evaluation.messlauf --fragen F01 --varianten bm25

# Vollständiger Vergleich (25 Fragen × 3 Varianten; API-Kosten)
python -m evaluation.messlauf
```

Die Antworten und Aufrufdetails landen zusätzlich unter `messungen/<datum>\_messlauf/runs.jsonl`. SQL-Auswertung: [`sql/kpi\_by\_variant.sql`](sql/kpi_by_variant.sql); manuelle Prüfung: [`Phase4/Klicktest-runs.md`](Phase4/Klicktest-runs.md). Probeeinträge sind in der Datenbank am Fragepräfix `\[Probe]` erkennbar.

Die zentrale Forschungsfrage lautet: **Ist die vollständige Recherche mit dem Tool gegenüber Claudes eigener Websuche schneller, günstiger und mindestens genauso zuverlässig?** Erst die Messläufe können diese Frage beantworten.

## Projektstruktur

```text
AlgorithmusProjekt/
├── README.md                  # Einstieg, Erklärung, Einrichtung und Befehle
├── AGENTS.md                  # Hinweise für Coding-Agenten
├── .mcp.json                  # MCP-Registrierung für Claude Code
├── requirements.txt          # Laufzeit- und Notebook-Abhängigkeiten
├── requirements-dev.txt      # Test-/Coverage-Abhängigkeiten
├── LICENSE                   # MIT-Lizenz
│
├── src/                      # Implementierung und Unittests
│   ├── sources/              # arXiv-API, Paper-Metadaten, Suchfilter
│   ├── chunking/             # Texte in überlappende Abschnitte zerlegen
│   ├── bm25/                 # Keyword-Index, BM25, Top-m-Auswahl
│   ├── vector\_search/        # Voyage-Embeddings, Cosinus, MMR
│   ├── ranking/              # RRF und Score-Normalisierung
│   ├── pipeline/             # Gesamtablauf und Konfiguration
│   ├── mcp\_server/           # MCP-Tool research\_papers
│   ├── storage/              # PostgreSQL-Zugriff
│   ├── cache/                # Such- und Embedding-Cache
│   └── evaluation/           # API-Messläufe und Messlogik
│
├── sql/                      # DB-Schema, Abfragen und KPI-Auswertung
│   └── uebungen/             # SQL-Beispiele und Datenbanktests
├── Phase2/                   # Gesamtablauf: Flowchart und Pseudocode
├── Phase3/                   # Interaktiver Prototyp (Jupyter Notebook)
├── Phase4/                   # Testkatalog, Testdokumentation, Klicktests
├── Phase5/                   # Reflexion, Grenzen und Optimierungsansätze
├── docs/                     # Algorithmusformeln, Entwürfe, ADRs, UML,
│                             # DB-Dokumentation und Evaluationsfragen
└── messungen/                # Messskripte, bisherige Versuche und Laufprotokolle
```

Für den Einstieg in die Architektur eignen sich besonders:

* [`Phase2/Pseudocode.md`](Phase2/Pseudocode.md) – vollständiger Ablauf und Entscheidungsregeln.
* [`Phase2/Flowchart\_RAG-Pipeline.drawio`](Phase2/Flowchart_RAG-Pipeline.drawio) – Ablaufdiagramm (mit draw.io öffnen).
* [`docs/adr/`](docs/adr/) – dokumentierte Architekturentscheidungen.
* [`Phase5/Reflexion.md`](Phase5/Reflexion.md) – bekannte technische und methodische Grenzen.
* [`docs/evaluation/testfragen.md`](docs/evaluation/testfragen.md) – Fragen und erwartete Quellen für die Messung.

## Fehlerbehebung

|Problem|Mögliche Ursache / Lösung|
|-|-|
|`ModuleNotFoundError: No module named 'pipeline'`|Aus dem Repository-Root starten und `PYTHONPATH=src` setzen.|
|Kein `VOYAGE\_API\_KEY`|Kein Fehler für die Grundfunktion: Die Pipeline nutzt dann ausschließlich BM25.|
|arXiv liefert keine Treffer|Englische Fachbegriffe verwenden; Zeitraum und Schreibweise prüfen.|
|arXiv nicht erreichbar / HTTP 429|Netzwerkverbindung, API-Verfügbarkeit und Anfragehäufigkeit prüfen. Automatischer Retry bei 429 ist nicht implementiert.|
|`Cache nicht verfügbar`|PostgreSQL prüfen oder bewusst ohne Cache weiterarbeiten.|
|Datenbanktests schlagen fehl|`algorithmusprojekt\_test`, Schema und DB-Berechtigungen prüfen.|
|Claude Code findet den MCP-Server nicht|Projektverzeichnis, `.mcp.json`, Python-Pfad und `PYTHONPATH` kontrollieren.|
|Evaluation mit `hybrid` startet nicht|`VOYAGE\_API\_KEY` setzen; für echte Claude-Läufe zusätzlich `ANTHROPIC\_API\_KEY`.|

## Sicherheit und Lizenz

* API-Schlüssel ausschließlich über Umgebungsvariablen oder nicht versionierte lokale Konfiguration bereitstellen; keine Secrets ins Repository committen.
* Der HTTP-MCP-Server enthält derzeit **keine Authentifizierung**. Lokal auf `127.0.0.1` binden oder nur hinter abgesichertem Reverse-Proxy/VPN zugänglich machen.
* arXiv-Einträge sind nicht automatisch peer-reviewed; DOI/Journal-Referenz sind lediglich Hilfsmerkmale.
* Die generierten KI-Antworten und ihre Quellen sollten für wissenschaftlich relevante Aussagen überprüft werden.

Lizenz: [MIT](LICENSE).

