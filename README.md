# AlgorithmusProjekt – RAG-Pipeline für die Recherche

Hackathon-Projekt von Gruppe 2 im FOM-Modul „Algorithmen & Datenstrukturen“.

## Problem

Bei der Recherche mit KI kommt es häufig zu Halluzinationen, und jede Recherche kostet Tokens und Zeit, weil das Sprachmodell selbst sucht und liest.

## Idee

Ein regelbasierter Auswahl-Algorithmus übernimmt die Recherche: Er durchsucht eine Wissensbasis, sortiert die Treffer vor und gibt nur die relevantesten Textabschnitte an das Sprachmodell zurück (Retrieval Augmented Generation). Bereitgestellt wird das als MCP-Tool, aufrufbar über einen MCP-Client wie Claude Desktop oder Claude Code.

Ziele:

- weniger Halluzinationen, weil das Modell auf belegten Quellen antwortet
- weniger Tokens und kürzere Laufzeit, weil die Vorauswahl algorithmisch passiert

## Bausteine

| # | Baustein | Verfahren |
|---|---|---|
| 1 | Chunking | Text in überlappende Abschnitte zerlegen |
| 2 | Vektorsuche | Cosine Similarity, Top-k mit Heap |
| 3 | Keyword-Suche | BM25 über einen invertierten Index |
| 4 | Hybrid-Ranking | Reciprocal Rank Fusion |
| 5 | Duplikat-Filter | Maximal Marginal Relevance, wählt die endgültigen k Abschnitte |
| 6 | MCP-Tool | Wrapper mit FastMCP |
| 7 | Evaluation | Testfragen mit bekannter Quelle, Vergleich der Varianten und des Tokenverbrauchs mit und ohne Tool |

Die Bausteine entstehen zuerst als eigenständige Übungen ohne Bibliotheken und werden danach zur Pipeline zusammengesteckt.

Die Pipeline arbeitet ohne Token-Budget: Die Größe der Antwort ist durch `k` und die Chunk-Größe begrenzt.

## Stand

Stand 15.11.2026: Alle Bausteine, die Pipeline und das MCP-Tool laufen, mit 325 Unittests (Coverage 97 %, Algorithmus-Module 100 %, siehe `Phase4/Testdokumentation.md`). Die Datenbank ist vollständig umgesetzt (sechs Tabellen, alle SQL-Abfragen, siehe [Datenbank](#datenbank)). Der MCP-Server schaltet einen Cache davor: Gleiche Suchen der letzten 7 Tage kommen aus der Datenbank (R13–R15), bekannte Chunks werden nicht neu eingebettet (R16). Das Skript für die Messläufe ist fertig, die Messung selbst steht noch aus (siehe [Messläufe](#messläufe)). Offen sind der Volltext statt Titel und Abstract und die Gewichtung nach Metadaten; Limitationen und Reflexion stehen in `Phase5/Reflexion.md`.

**Bekannte Einschränkungen** (ADR 0004, Messungen in `messungen/2026-10-19_review-pr24/`): Auf Titel und Abstract filtert die BM25-Vorauswahl nur Chunks ganz ohne Schlagwort aus, und das Hauptschlagwort bekommt eine IDF nahe null, weil arXiv die Dokumente gerade wegen der Schlagwörter liefert. Beides löst erst der Volltext mit Datenbank-Cache. Aufgaben und Fortschritt stehen in den [Issues](https://github.com/luca-1893/AlgorithmusProjekt/issues), gruppiert nach den [Phasen des Hackathons](https://github.com/luca-1893/AlgorithmusProjekt/milestones).

## Hackathon-Phasen

| Phase | Inhalt | Termin |
|---|---|---|
| 1 | Problemdefinition & Use Case | 21.09.2026 |
| 2 | Algorithmischer Entwurf | 05.10.2026 |
| 3 | Erste Implementierung | 19.10.2026 |
| 4 | Test & Validierung | 09.11.2026 |
| 5 | Optimierung & Reflexion | 16.11.2026 |
| 6 | Pitch | 30.11.2026 |

## Projektstruktur

```
AlgorithmusProjekt/
├── Phase2/
│   ├── Flowchart_RAG-Pipeline.drawio   # Flowchart mit Entscheidungsregeln R1–R16
│   └── Pseudocode.md                   # Gesamtablauf, Start-/Endbedingungen, Regeln
├── Phase3/
│   └── Prototyp.ipynb                  # lauffähiger Prototyp
├── Phase4/
│   ├── Testdokumentation.md            # Testkategorien, Coverage, ausgewählte Fälle, Abweichungen
│   ├── Testkatalog.md                  # alle Unittests, erzeugt von testkatalog.py
│   └── Klicktest-runs.md               # Anleitung: Messläufe in runs von Hand prüfen
├── Phase5/
│   └── Reflexion.md                    # Annahmen, Limitationen, Leitfragen
├── src/
│   ├── bm25/            # Tokenizer, invertierter Index, BM25, top_m
│   ├── chunking/        # Chunks mit Überlappung
│   ├── sources/         # arXiv-Anbindung, Dokumente, Suchfilter
│   ├── vector_search/   # Cosinus, Top-k, Voyage-Einbetter, MMR
│   ├── ranking/         # Rangfusion (RRF), Normalisierung
│   ├── pipeline/        # verbindet alle Bausteine
│   ├── mcp_server/      # MCP-Tool research_papers
│   ├── storage/         # PostgreSQL: eine Funktion je SQL-Datei
│   ├── cache/           # Datenbank-Cache vor arXiv und Voyage (R13–R16)
│   └── evaluation/      # Messläufe mit der Claude API, schreibt in runs
├── sql/                 # SQL-Dateien (Luca): schema.sql, Abfragen
│   └── uebungen/        # Testfälle zum Ausprobieren in DataGrip
├── messungen/           # Messskripte und Ergebnisse, z. B. zum Review von PR #24
├── docs/
│   ├── <modul>/         # Pseudocode und Formelsammlungen je Modul
│   ├── adr/             # Architekturentscheidungen
│   ├── storage/         # SQL-Anforderungen, Schema-Entwurf, ER-Diagramm, SQL-Cheatsheet
│   ├── evaluation/      # Leitfragen und die 25 Messfragen
│   ├── journal.md       # Arbeitsjournal
│   └── uml/             # UML-Diagramme (PlantUML)
├── .mcp.json            # MCP-Tool für Claude Code (macOS/Linux-Pfade)
├── requirements.txt
├── requirements-dev.txt # coverage
├── README.md
└── LICENSE
```

## Einrichtung

Python 3.15 und eine virtuelle Umgebung im Projektordner:

```
brew install python@3.15
python3.15 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Unter Windows (PowerShell):

```
py -3.15 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
setx VOYAGE_API_KEY "dein-schlüssel"
```

`setx` gilt erst in neu geöffneten Terminals. Die Pfade in `.mcp.json` sind für macOS/Linux; unter Windows dort `.venv\\Scripts\\python.exe` eintragen.

In PyCharm `.venv/bin/python` (Windows: `.venv\Scripts\python.exe`) als Interpreter wählen. Für die Vektorsuche muss `VOYAGE_API_KEY` gesetzt sein, z. B. in `~/.zshenv`; ohne Schlüssel arbeitet die Pipeline nur mit BM25. Für die Messläufe braucht es zusätzlich `ANTHROPIC_API_KEY`.

## Prototyp

`Phase3/Prototyp.ipynb` zeigt die Bausteine einzeln, die ganze Pipeline gegen arXiv (nur BM25 und hybrid), die JSON-Ausgabe, eine Schätzung der Token-Ersparnis und die Fehlerfälle. Starten mit `jupyter notebook Phase3/Prototyp.ipynb` aus der aktivierten Umgebung.

## MCP-Tool

Der Server bietet ein Tool, `research_papers(keywords, k = 5, question = "", published_after = "", peer_reviewed_only = false)`, und gibt die ausgewählten Abschnitte mit Titel, Autoren, Datum und Link als JSON zurück, dazu `warnings`, z. B. „Dokumente aus dem Cache“ oder „Cache nicht verfügbar“. Ist die Datenbank nicht erreichbar, läuft das Tool ohne Cache weiter.

Lokal über stdio, z. B. für Claude Code oder Claude Desktop:

```
PYTHONPATH=src .venv/bin/python -m mcp_server
```

In diesem Projekt ist das Tool für Claude Code schon in `.mcp.json` eingetragen; Claude Code fragt beim ersten Start, ob es den Server nutzen darf.

Als Webdienst auf dem Server (Endpunkt `/mcp`):

```
PYTHONPATH=src .venv/bin/python -m mcp_server --transport http --host 0.0.0.0 --port 8000
```

Über HTTP gibt es noch keine Anmeldung. Den Dienst deshalb nur hinter einem abgesicherten Zugang betreiben, z. B. VPN oder Reverse-Proxy mit Token.

## Datenbank

PostgreSQL 18 per Homebrew, Datenbanken `algorithmusprojekt` und `algorithmusprojekt_test`:

```
brew install postgresql@18
brew services start postgresql@18
/opt/homebrew/opt/postgresql@18/bin/createdb algorithmusprojekt
/opt/homebrew/opt/postgresql@18/bin/createdb algorithmusprojekt_test
```

Das Schema hat sechs Tabellen: `documents` (ein Eintrag je Quelle, mit Volltext), `chunks`, `chunk_embeddings` (ein Vektor je Chunk und Modell), `searches` und `search_documents` (Such-Cache, 7 Tage gültig) sowie `runs` (Messläufe der Varianten `agent_websearch`, `bm25` und `hybrid`).

| Datei | Inhalt | Stand |
|---|---|---|
| `docs/storage/sql-aufgaben.md` | Anforderungen an die SQL-Dateien | fertig |
| `docs/storage/schema-entwurf.md` | Tabellen, Spalten und 29 begründete Entscheidungen | fertig |
| `docs/storage/schema.drawio` | ER-Diagramm (mit draw.io öffnen) | fertig |
| `docs/storage/sql-cheatsheet.md` | Syntax und Beispiele aus den SQL-Übungen | fertig |
| `sql/schema.sql` | alle sechs Tabellen und zwei Indizes (ADR 0005), mehrfach ausführbar | fertig |
| `sql/uebungen/test_*.sql` | Testfälle für die Regeln jeder Tabelle | fertig |
| übrige Dateien in `sql/` | je eine Abfrage für Dokumente, Chunks, Vektoren, Such-Cache und Messläufe; aufgerufen von `src/storage/storage.py` | fertig |

Schema anlegen bzw. auf den aktuellen Stand prüfen (bestehende Tabellen und Daten bleiben unverändert):

```
/opt/homebrew/opt/postgresql@18/bin/psql -d algorithmusprojekt -f sql/schema.sql
/opt/homebrew/opt/postgresql@18/bin/psql -d algorithmusprojekt_test -f sql/schema.sql
```

Die Tests nutzen `algorithmusprojekt_test`, das MCP-Tool und die Messläufe `algorithmusprojekt` (änderbar über `DATABASE_URL`).

## Messläufe

Jede der 25 Fragen aus `docs/evaluation/testfragen.md` wird in drei Varianten beantwortet: `agent_websearch` (Websuche von Claude, ohne Tool), `bm25` und `hybrid` (mit `research_papers`). Gleiches Modell und gleicher System-Prompt für alle, ohne Cache. Jeder Lauf landet in `runs`, mit den Tokens aus der API-Antwort, der Dauer und `found_source` (steht die erwartete arXiv-ID in der Antwort?). Antworten und Tool-Aufrufe stehen zusätzlich in `messungen/<datum>_messlauf/runs.jsonl`.

```
PYTHONPATH=src .venv/bin/python -m evaluation.messlauf                    # alle 25 × 3, kostet API-Guthaben
PYTHONPATH=src .venv/bin/python -m evaluation.messlauf --fragen F01,F14   # nur einzelne Fragen
PYTHONPATH=src .venv/bin/python -m evaluation.messlauf --probe            # ohne API und arXiv, zum Prüfen von runs
```

Probeläufe stehen mit „[Probe]“ vor der Frage in `runs` und lassen sich mit `DELETE FROM runs WHERE question LIKE '[Probe]%';` wieder entfernen. Die Auswertung macht `sql/kpi_by_variant.sql`. Anleitung zum Prüfen von Hand: `Phase4/Klicktest-runs.md`.

## Tests ausführen

Alle Module auf einmal, aus dem Projektordner:

```
python -m unittest discover -s src -t src
```

Mit Coverage (`pip install -r requirements-dev.txt`):

```
python -m coverage run --branch -m unittest discover -s src -t src
python -m coverage report --omit="*/test_*,*/__init__.py"
```

Einzelnes Modul ohne Abhängigkeit zu anderen Modulen, aus seinem Ordner, z. B. `src/bm25`. Pipeline und MCP-Server importieren andere Module und laufen deshalb nur über den Befehl oben; die MCP-Tests brauchen außerdem die `.venv` mit Python 3.15:

```
python -m unittest
```

## Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).
