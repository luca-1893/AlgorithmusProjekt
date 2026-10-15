# Arbeitsjournal

## 2026-10-10

- Projektziel festgehalten: hybride RAG-Pipeline für die Recherche als MCP-Tool; README und früherer Entwurf im Repo beschrieben andere Algorithmen.
- Kanban-Board als GitHub Project angelegt (Spalten Backlog, Next, In Progress, Review, Done), Karten für die acht Bausteine, die Pflichtabgaben des Hackathons und Milestones für die Phasen 2 bis 6.
- Repo aufgeräumt: README neu geschrieben, `.gitignore` und `docs/` angelegt.
- Flowchart der Pipeline als Entwurf in `Phase2/Flowchart_RAG-Pipeline.drawio` (zwei Seiten: Anfrage, Indexaufbau); Audit und Pseudocode stehen noch aus.
- Entscheidung: kein Token-Budget als Parameter; die Antwortgröße ist durch `k` und die Chunk-Größe begrenzt. Der Knapsack bleibt als Lernübung außerhalb der Pipeline. Flowchart entsprechend umgebaut (MMR als Schleife).
- KPI-Idee festgehalten: Tokenverbrauch derselben Anfrage mit und ohne MCP-Tool messen, Delta als Ersparnis.

## 2026-10-15

- Rollen aus Zeitgründen neu verteilt: Luca baut BM25 und schreibt das SQL selbst, die übrigen Module aus dem Flowchart entstehen mit Claude, jeweils mit Pseudocode, Unittests und Review nach jeder Funktion.
- Chunking: `split_into_chunks` mit Pseudocode und 13 Unittests entworfen, wartet auf Review.
- Entscheidungen: Zielversion Python 3.15; Deployment auf eigenem Server; Embeddings über eine API mit Schlüssel (ADR 0001, Anbieter offen); PostgreSQL als Datenbank für Cache, Duplikaterkennung und Messläufe (ADR 0002).
- Quelle: arXiv angebunden (`src/sources/`), zunächst nur Titel und Abstract aus Performance-Gründen. Schlagwörter werden mit OR verknüpft, die Feinauswahl macht BM25.
- Chunking um die Struktur `Chunk` erweitert; Chunks verweisen nur über `document_id` auf ihr Dokument, passend zum geplanten Datenbankschema.
- Vektorsuche (`src/vector_search/`): Cosinus-Ähnlichkeit, Top-k mit begrenztem Min-Heap, Einbetter-Schnittstelle ohne konkreten Anbieter, MMR-Auswahl.
- Ranking (`src/ranking/`): Reciprocal Rank Fusion und Min-Max-Normalisierung. Gewichtung nach Metadaten fehlt noch, die Kriterien legt Luca fest.
- Code ohne Kommentare, nur kurze Docstrings (Lucas Vorgabe).
