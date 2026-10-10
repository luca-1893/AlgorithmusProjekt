# AlgorithmusProjekt – RAG-Pipeline für die Recherche

Hackathon-Projekt von Gruppe 2 im FOM-Modul „Algorithmen & Datenstrukturen“.

## Problem

Bei der Recherche mit KI kommt es häufig zu Halluzinationen, und jede Recherche kostet Tokens und Zeit, weil das Sprachmodell selbst sucht und liest.

## Idee

Ein regelbasierter Auswahl-Algorithmus übernimmt die Recherche: Er durchsucht eine Wissensbasis, sortiert die Treffer vor und gibt nur die relevantesten Textabschnitte an das Sprachmodell zurück (Retrieval Augmented Generation). Bereitgestellt wird das als MCP-Tool, aufrufbar über einen MCP-Client wie Claude Desktop oder Claude Code.

Ziele:

- weniger Halluzinationen, weil das Modell auf belegten Quellen antwortet
- weniger Tokens und kürzere Laufzeit, weil die Vorauswahl algorithmisch passiert

## Geplante Bausteine

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

Das Projekt ist in der Konzeptphase, es gibt noch keinen Code. Aufgaben und Fortschritt stehen in den [Issues](https://github.com/luca-1893/AlgorithmusProjekt/issues), gruppiert nach den [Phasen des Hackathons](https://github.com/luca-1893/AlgorithmusProjekt/milestones).

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
│   ├── Flowchart_RAG-Pipeline.drawio   # Flowchart der Pipeline (Anfrage, Indexaufbau)
│   └── Pseudocode.drawio               # früher Entwurf: Keyword-Satzfilter
├── docs/
│   ├── journal.md          # Arbeitsjournal
│   └── uml/                # UML-Diagramme (PlantUML)
├── README.md
└── LICENSE
```

## Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).
