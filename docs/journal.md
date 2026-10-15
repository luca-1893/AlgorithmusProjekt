# Arbeitsjournal

## 2026-10-10

- Projektziel festgehalten: hybride RAG-Pipeline für die Recherche als MCP-Tool; README und früherer Entwurf im Repo beschrieben andere Algorithmen.
- Kanban-Board als GitHub Project angelegt (Spalten Backlog, Next, In Progress, Review, Done), Karten für die acht Bausteine, die Pflichtabgaben des Hackathons und Milestones für die Phasen 2 bis 6.
- Repo aufgeräumt: README neu geschrieben, `.gitignore` und `docs/` angelegt.
- Flowchart der Pipeline als Entwurf in `Phase2/Flowchart_RAG-Pipeline.drawio` (zwei Seiten: Anfrage, Indexaufbau); Audit und Pseudocode stehen noch aus.
- Entscheidung: kein Token-Budget als Parameter; die Antwortgröße ist durch `k` und die Chunk-Größe begrenzt. Der Knapsack bleibt als Lernübung außerhalb der Pipeline. Flowchart entsprechend umgebaut (MMR als Schleife).
- KPI-Idee festgehalten: Tokenverbrauch derselben Anfrage mit und ohne MCP-Tool messen, Delta als Ersparnis.

## 2026-10-12

- BM25 (Karte #4) als eigenständige Übung begonnen: reines Python, nur Standardbibliothek, ein Mini-Korpus aus drei Einkaufszetteln statt echter Chunks.
- Formeln geklärt und in `docs/bm25/bm25-formelsammlung.md` festgehalten. Wichtigster Unterschied: Termhäufigkeit `f(q,D)` (wie oft im Dokument) gegen Dokumenthäufigkeit `n(q)` (in wie vielen Dokumenten).
- Altes `Phase2/Pseudocode.drawio` (Keyword-Satzfilter) entfernt, es beschrieb einen anderen Algorithmus.
- Tokenizer entworfen, als Pseudocode ausgearbeitet und mit Unittests umgesetzt. Laufzeit O(n), n = Zeichen. Ausgabe ist eine Liste, kein Set, weil `f(q,D)` und `|D|` die Duplikate brauchen.

## 2026-10-13

- Handrechnung für „apfel milch“ mit `k1 = 1.5`, `b = 0.75`: Z1 = 0.694, Z3 = 0.767. Das ist die Referenz für den Score-Test.
- Tokenizer überarbeitet: `casefold` statt `lower` („Strasse“ = „Straße“); Bindestrich und Apostroph verbinden („E-Mail“ → `email`, „don't“ → `dont`); Satzzeichen und Gedankenstriche trennen („and/or“ → `and`, `or`; „10–20“ → `10`, `20`). Regex bewusst vermieden.
- Bekannte Grenzen: Homonyme wie Arm/arm verschmelzen; „baum“ findet „Apfel-Baum“ nicht mehr; „z.B.“ wird zu `z`, `b`. Für eine Vorauswahl vor der Vektorsuche akzeptiert.
- Keine Queue zwischen Tokenizer und Index: Der Code läuft synchron, Aufbau und Abfrage sind getrennte Phasen.

## 2026-10-15

- Invertierter Index `build_index`: Wort → (Dok-ID → Anzahl), dazu Dokumentlängen, N und avgdl. Dok-ID = Position in der Liste; leere Dokumente werden nach dem Tokenisieren übersprungen, die IDs der anderen bleiben stabil. Laufzeit O(T), T = Tokens. `k1` und `b` gehören nicht in den Index, damit man sie ohne Neuaufbau ändern kann.
- IDF mit +1 (Lucene), gleichwertig zu `ln((N + 1) / (df + 0.5))` und nie negativ; begründet in ADR 0003. `compute_idf(df, N)` bekommt nur Zahlen, ein unbekanntes Wort hat df = 0.
- Score in zwei Funktionen: Beitrag eines Worts zu einem Dokument und Score eines Dokuments für die ganze Anfrage. Ergebnis stimmt mit der Handrechnung überein.
- Anfrage nach dem Tokenisieren als Set dedupliziert: Doppelte Schlagwörter sind eher Zufall oder Halluzination.
- `top_m`: nur Dokumente aus den Postings der Anfragewörter sind Kandidaten (Score > 0 automatisch), IDF einmal pro Wort statt pro Dokument, Top-m per Heap mit `(−score, doc_id)` und `nsmallest`, bei Gleichstand die kleinere Dok-ID zuerst. Laufzeit O(P + C · |q| + C · log m) statt O(C · log C) beim kompletten Sortieren.
- Experiment mit k1 und b: k1 steuert, wie sehr Wiederholung zählt, b, wie sehr Länge bestraft wird. Das kurze Dokument mit zweimal „apfel“ überholt das lange mit beiden Wörtern erst ab k1 ≈ 3 und nur bei b > 0; bei b = 0 nie. Dabei Division durch null bei `k1 = 0` gefunden und behoben (`f = 0` ergibt Beitrag 0).
- 51 Unittests, Edge Cases teils mit KI-Hilfe gesammelt. Lehre: Ändert sich eine Designentscheidung, müssen alle Tests gesucht werden, die die alte festhalten.
