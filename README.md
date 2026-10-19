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

Phase 3 (erste Implementierung) ist umgesetzt: Alle Bausteine, die Pipeline und das MCP-Tool laufen, mit über 240 Unittests. Offen sind die Datenbank-Anbindung, die Gewichtung nach Metadaten und die Evaluation.

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
│   ├── Flowchart_RAG-Pipeline.drawio   # Flowchart mit Entscheidungsregeln R1–R12
│   └── Pseudocode.md                   # Gesamtablauf, Start-/Endbedingungen, Regeln
├── Phase3/
│   └── Prototyp.ipynb                  # lauffähiger Prototyp
├── src/
│   ├── bm25/            # Tokenizer, invertierter Index, BM25, top_m
│   ├── chunking/        # Chunks mit Überlappung
│   ├── sources/         # arXiv-Anbindung, Dokumente, Suchfilter
│   ├── vector_search/   # Cosinus, Top-k, Voyage-Einbetter, MMR
│   ├── ranking/         # Rangfusion (RRF), Normalisierung
│   ├── pipeline/        # verbindet alle Bausteine
│   ├── mcp_server/      # MCP-Tool research_papers
│   └── storage/         # PostgreSQL-Verbindung
├── sql/                 # SQL-Dateien (Luca)
├── messungen/           # Messskripte und Ergebnisse, z. B. zum Review von PR #24
├── docs/
│   ├── <modul>/         # Pseudocode und Formelsammlungen je Modul
│   ├── adr/             # Architekturentscheidungen
│   ├── storage/         # Anforderungen an die SQL-Dateien
│   ├── journal.md       # Arbeitsjournal
│   └── uml/             # UML-Diagramme (PlantUML)
├── .mcp.json            # MCP-Tool für Claude Code (macOS/Linux-Pfade)
├── requirements.txt
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

In PyCharm `.venv/bin/python` (Windows: `.venv\Scripts\python.exe`) als Interpreter wählen. Für die Vektorsuche muss `VOYAGE_API_KEY` gesetzt sein, z. B. in `~/.zshenv`; ohne Schlüssel arbeitet die Pipeline nur mit BM25.

## Prototyp

`Phase3/Prototyp.ipynb` zeigt die Bausteine einzeln, die ganze Pipeline gegen arXiv (nur BM25 und hybrid), die JSON-Ausgabe, eine Schätzung der Token-Ersparnis und die Fehlerfälle. Starten mit `jupyter notebook Phase3/Prototyp.ipynb` aus der aktivierten Umgebung.

## MCP-Tool

Der Server bietet ein Tool, `research_papers(keywords, k = 5, question = "")`, und gibt die ausgewählten Abschnitte mit Titel, Autoren, Datum und Link als JSON zurück.

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

Die SQL-Dateien liegen in `sql/`, die Anforderungen in `docs/storage/sql-aufgaben.md`.

## Tests ausführen

Alle Module auf einmal, aus dem Projektordner:

```
python -m unittest discover -s src -t src
```

Einzelnes Modul ohne Abhängigkeit zu anderen Modulen, aus seinem Ordner, z. B. `src/bm25`. Pipeline und MCP-Server importieren andere Module und laufen deshalb nur über den Befehl oben; die MCP-Tests brauchen außerdem die `.venv` mit Python 3.15:

```
python -m unittest
```

## Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).
