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
- Rollen aus Zeitgründen neu verteilt: Luca baut BM25 und schreibt das SQL selbst, die übrigen Module aus dem Flowchart entstehen mit Claude, jeweils mit Pseudocode, Unittests und Review nach jeder Funktion.
- Chunking: `split_into_chunks` mit Pseudocode und 13 Unittests entworfen, wartet auf Review.
- Entscheidungen: Zielversion Python 3.15; Deployment auf eigenem Server; Embeddings über eine API mit Schlüssel (ADR 0001, Anbieter offen); PostgreSQL als Datenbank für Cache, Duplikaterkennung und Messläufe (ADR 0002).
- Quelle: arXiv angebunden (`src/sources/`), zunächst nur Titel und Abstract aus Performance-Gründen. Schlagwörter werden mit OR verknüpft, die Feinauswahl macht BM25.
- Chunking um die Struktur `Chunk` erweitert; Chunks verweisen nur über `document_id` auf ihr Dokument, passend zum geplanten Datenbankschema.
- Vektorsuche (`src/vector_search/`): Cosinus-Ähnlichkeit, Top-k mit begrenztem Min-Heap, Einbetter-Schnittstelle ohne konkreten Anbieter, MMR-Auswahl.
- Ranking (`src/ranking/`): Reciprocal Rank Fusion und Min-Max-Normalisierung. Gewichtung nach Metadaten fehlt noch, die Kriterien legt Luca fest.
- Code ohne Kommentare, nur kurze Docstrings (Lucas Vorgabe); Ausnahme ist mathematischer Code wie BM25, `top_k`, MMR und RRF, dort erklären kurze Kommentare die Formeln.

## 2026-10-16

- BM25 per PR #23 nach `master` gemergt. Die Regel auf `master` sperrte jede Änderung, auch über Pull Requests („Restrict updates“); Luca hat sie entfernt, Löschschutz, Force-Push-Sperre und PR-Pflicht bleiben.
- Übrige Module auf das Niveau des BM25-Moduls gebracht: eine Testklasse pro Funktion, zusätzliche Invarianten- und Randfall-Tests (z. B. Eingabe wird nicht verändert, Top-k stimmt mit vollständiger Sortierung überein), Laufzeit und bekannte Grenzen im Pseudocode, Formelsammlungen mit Handrechnung für Vektorsuche, MMR und RRF.
- Fehler gefunden: Ein Anführungszeichen im Schlagwort hätte die arXiv-Phrase beendet; es wird jetzt entfernt.
- Module zu Paketen gemacht: Jedes `__init__.py` reicht sein Modul weiter, dadurch bleiben die bestehenden Tests unverändert und alle laufen mit `python3 -m unittest discover -s src -t src`.
- Pipeline (`src/pipeline/`): Quelle, Chunking, BM25-Vorauswahl, dann entweder direkt die besten k (ohne Einbetter) oder hybrid mit Vektorsuche, RRF und MMR. Fällt der Einbetter aus, liefert sie BM25-Ergebnisse mit Hinweis. Ausgabe als JSON-fähiges Dict für das MCP-Tool. Ohne Einbetter gegen das echte arXiv getestet: 0,5 s, drei passende Paper.
- Embedding-Anbieter entschieden: Voyage AI (ADR 0001, Nachtrag). `VoyageEmbedder` nur mit Standardbibliothek, Schlüssel aus `VOYAGE_API_KEY`, Modell `voyage-4`. Anfrage und Chunks werden getrennt eingebettet (`input_type`), weil Voyage beide unterschiedlich darstellt. Fehler führen zum BM25-Fallback.
- Erster Lauf gegen arXiv und Voyage („UML, class diagram, semantics“, k = 5, deutsche Frage nach der formalen Semantik von Klassendiagrammen): BM25 allein 0,1 s, hybrid 1,3 s. Hybrid ersetzt „From user requirements to UML class diagram“ durch „A Formal Semantic for UML 2.0 Activity Diagram“, passt also besser zur Frage, obwohl sie deutsch und die Abstracts englisch sind.
- Flowchart auf den umgesetzten Stand gebracht: Frage als optionale Eingabe, Abzweig ohne Einbetter (nur BM25), Kandidaten aus BM25 oder bei null Treffern alle Chunks, Voyage mit getrennter Einbettung von Anfrage und Kandidaten, Fallback auf BM25 bei Einbettungsfehler, RRF und MMR, Ausgabe als JSON mit Hinweisen. Der Schritt „Dokument laden und in Markdown umwandeln“ ist entfallen, weil nur Titel und Abstract verarbeitet werden.
- Python 3.15.0 per Homebrew installiert, virtuelle Umgebung `.venv` im Projekt. Alle 200 Tests laufen auf 3.15; FastMCP 4.1.0 lässt sich installieren und importieren, das MCP-Tool ist damit nicht blockiert.
- Prototyp-Notebook `Phase3/Prototyp.ipynb`: Bausteine einzeln mit den Handrechnungen, die ganze Pipeline gegen arXiv mit 20 Dokumenten (nur BM25: 6 ms ohne Netzwerk; hybrid: 2,7 s inklusive Voyage), Vergleich der Rangfolgen, JSON-Ausgabe, geschätzte Ersparnis von 69 % (5 Chunks statt 20 Abstracts, Zeichen geteilt durch 4) und sechs Fehler- und Sonderfälle. Läuft ohne Schlüssel nur mit BM25 und ohne Internet mit eingebauten Beispieldokumenten. `requirements.txt` angelegt.
- MCP-Server mit FastMCP (`src/mcp_server/`): ein Tool `research_papers(keywords, k, question)`, nur lesend, k zwischen 1 und 20; ungültige Eingaben und Quellenfehler kommen als Tool-Fehler beim Sprachmodell an, der Server läuft weiter. Start über stdio (lokal) oder HTTP (Server). Voyage wird genutzt, wenn der Schlüssel gesetzt ist, sonst nur BM25. Als echter Prozess über stdio getestet: „Wie reduziert RAG Halluzinationen?“ liefert in 2,4 s drei passende Paper. `.mcp.json` trägt das Tool für Claude Code im Projekt ein. Offen: Anmeldung für den HTTP-Betrieb.
- Filter: `SearchFilter` mit Zeitraum, Kategorien und „nur begutachtet“. Zeitraum und Kategorien filtert arXiv selbst (`submittedDate`, `cat:`), „nur begutachtet“ behält nur Paper mit Zeitschriftenverweis oder DOI; dafür wird das Dreifache geholt. Seitenzahl ist kein Filter, weil sie nur unregelmäßig im Kommentarfeld steht. Durchgereicht über Pipeline und MCP-Tool (`published_after`, `peer_reviewed_only`). Live geprüft. Beobachtung: Zwei arXiv-Einträge (1409.6928 und 1409.6919) tragen dieselbe DOI, die DOI eignet sich also zur Duplikaterkennung in der Datenbank.
- PostgreSQL 18.6 lokal per Homebrew eingerichtet, Datenbanken `algorithmusprojekt` und `algorithmusprojekt_test`, Treiber `psycopg` 3.3.6. `src/storage/` baut die Verbindung auf (`DATABASE_URL`) und führt SQL-Dateien aus `sql/` aus; das SQL selbst schreibt Luca, die Anforderungen dafür stehen in `docs/storage/sql-aufgaben.md`.
- Phase-2-Nachzug: `Phase2/Pseudocode.md` mit Eingaben und Parametern, Start- und Endbedingungen, Gesamtalgorithmus, Entscheidungsregeln R1 bis R12, Schleifen S1 und S2, Komplexität und Annahmen. Die Rauten im Flowchart tragen dieselben Nummern. README-Projektstruktur und -Stand aktualisiert, Einrichtung unter Windows ergänzt.

## 2026-10-19

- Cache-Verhalten entschieden und in `Phase2/Pseudocode.md` und das Flowchart übernommen (R13 bis R16): Der Such-Cache gilt 7 Tage, weil täglich neue Paper erscheinen. Dokumente und Embeddings veralten nicht und bleiben unbegrenzt, Embeddings gebunden an Modell und Chunk-Parameter. Ist die Datenbank nicht erreichbar, läuft die Recherche ohne Cache weiter. Umsetzung folgt mit dem SQL.
- DataGrip auf dem Mac installiert; System-Prompt für einen SQL-Tutor-Thread erstellt, weil Luca SQL von Grund auf lernt.

## 2026-10-20

- SQL-Grundlagen in DataGrip an einer Übungs-Bibliothek (`buch`, `buch2`, `ausleihe`) selbst geschrieben: Tabellen mit passenden Typen, WHERE, ORDER BY, LIMIT, PRIMARY KEY, NOT NULL, UNIQUE, Fremdschlüssel mit `ON DELETE CASCADE`, INNER und LEFT JOIN.
- Erlebt statt gelesen: `= NULL` liefert nie einen Treffer, also `IS NULL`; ein Insert mit mehreren Zeilen scheitert ganz (Atomarität); `CREATE TABLE` überschreibt keine bestehende Tabelle; Werte ohne Anführungszeichen werden gerechnet (`3-930685-28-0` wird zu −930710).
- Übungs-Datenbank korrigiert: Die ersten Tabellen lagen versehentlich in `postgres`; Prüfung ab jetzt mit `SELECT current_database()`. Syntax-Übungen laufen weiter über sqlbolt.com (bis Lektion 12).

## 2026-10-28

- Schema-Entwurf in `docs/storage/schema-entwurf.md` begonnen, Entscheidungen jeweils mit Begründung.
- `documents`: künstliche ID mit `UNIQUE (source, source_id)`, damit weitere Quellen dieselben IDs vergeben können; `source_id` ohne Versionsnummer, weil v1 und v2 dasselbe Paper sind. Eine Zeile ist ein Quell-Eintrag, kein Werk: Die DOI ist deshalb nicht eindeutig, Duplikate findet eine Abfrage mit `GROUP BY … HAVING`.
- Fehlende Werte als `NULL` statt `''`; Autoren und Kategorien als Array, weil arXiv dazu nur Namen und Kürzel liefert (keine Uni, keine ORCID).
- Volltext wird gespeichert, weil die Chunks mit Overlap rund 25 % mehr Platz brauchen (6.000 Wörter ergeben 38 Chunks mit 7.600 Wörtern). Herkunft `html`, `pdf` oder `abstract`; Dokumente ohne Volltext bleiben mit dem Abstract im Cache. Chunk-Parameter stehen am Dokument und werden wie in `split_into_chunks` per `CHECK` geprüft.
- `chunks` mit PK `(document_id, position)` und `CASCADE`; Such-Cache als m:n (`searches`, `search_documents`), Schlagwörter in Python kleingeschrieben und sortiert, gespeichert wird die Reihenfolge von arXiv, kein BM25-Score.

## 2026-10-29

- Entwurf abgeschlossen: `searches` (Zeitraum als `date`, `NULL` heißt keine Grenze; `searched_at` als `timestamptz` von der Datenbank), `runs` mit den Varianten `agent_websearch`, `bm25` und `hybrid` (Vergleich mit einem Agenten, der selbst im Web recherchiert), exakten Tokens und Dauer in ms, `found_source` später bewertet, Startzeitpunkt von Python. `chunk_embeddings` als `real[]` je Chunk und Modell, ohne `pgvector`. Insgesamt 29 Entscheidungen, dazu ein ER-Diagramm (`docs/storage/schema.drawio`) und ein SQL-Cheatsheet (`docs/storage/sql-cheatsheet.md`).
- `documents` in `sql/schema.sql` umgesetzt (IDENTITY, `UNIQUE (source, source_id)`, `CHECK` für Herkunft, Chunk-Parameter und „Volltext fehlt genau bei `origin = 'abstract'`“, `DEFAULT now()` und `'{}'`) und mit acht Testfällen in `sql/uebungen/test_documents.sql` geprüft: Alle Regeln greifen wie geplant.
- Gelernt: Eine Schemaänderung kommt wegen `IF NOT EXISTS` erst nach einem `DROP` an, das nur in der Test-Datenbank und nie in `schema.sql` steht. Gescheiterte Inserts verbrauchen IDENTITY-Nummern. DataGrip bricht beim Ausführen mehrerer Statements nach dem ersten Fehler ab.
- Nächster Schritt: `CHECK`-Regeln benennen, weil Namen wie `documents_check1` in Fehlermeldungen nicht verraten, welche Regel verletzt wurde; danach die übrigen fünf Tabellen.
