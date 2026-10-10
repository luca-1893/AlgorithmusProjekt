# Arbeitsjournal

## 2026-10-10

- Projektziel festgehalten: hybride RAG-Pipeline für die Recherche als MCP-Tool; README und früherer Entwurf im Repo beschrieben andere Algorithmen.
- Kanban-Board als GitHub Project angelegt (Spalten Backlog, Next, In Progress, Review, Done), Karten für die acht Bausteine, die Pflichtabgaben des Hackathons und Milestones für die Phasen 2 bis 6.
- Repo aufgeräumt: README neu geschrieben, `.gitignore` und `docs/` angelegt.
- Flowchart der Pipeline als Entwurf in `Phase2/Flowchart_RAG-Pipeline.drawio` (zwei Seiten: Anfrage, Indexaufbau); Audit und Pseudocode stehen noch aus.
- Entscheidung: kein Token-Budget als Parameter; die Antwortgröße ist durch `k` und die Chunk-Größe begrenzt. Der Knapsack bleibt als Lernübung außerhalb der Pipeline. Flowchart entsprechend umgebaut (MMR als Schleife).
- KPI-Idee festgehalten: Tokenverbrauch derselben Anfrage mit und ohne MCP-Tool messen, Delta als Ersparnis.
