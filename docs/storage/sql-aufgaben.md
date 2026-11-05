# Datenbank – Aufgaben für Luca (SQL)

Das SQL schreibst du selbst (Karte #20). Die Python-Seite steht in `src/storage/storage.py`: Sie baut die Verbindung auf und führt deine Dateien aus `sql/` aus. Hier steht, **was** die Dateien leisten müssen, nicht wie.

## Verbindung (DataGrip)

| Feld | Lokal |
|---|---|
| Host / Port | `localhost` / `5432` |
| Benutzer | `lucafeest`, ohne Passwort (lokal `trust`) |
| Datenbank | `algorithmusprojekt` (Arbeit), `algorithmusprojekt_test` (Tests) |
| Server | PostgreSQL 18.6 per Homebrew, läuft als Dienst (`brew services stop postgresql@18` zum Anhalten) |

Python liest die Verbindung aus `DATABASE_URL`, Standard ist `postgresql:///algorithmusprojekt`. Auf dem Server setzt du `DATABASE_URL` mit eigenem Benutzer und Passwort.

## Spielregeln für die Dateien

- Eine Datei pro Zweck: `sql/<name>.sql`; Python lädt sie mit `load_sql("<name>")`.
- Parameter als benannte Platzhalter im psycopg-Stil: `%(document_id)s`, nicht `$1` und nicht per String-Verkettung (SQL-Injection).
- `schema.sql` muss mehrfach ausführbar sein, ohne Fehler und ohne Datenverlust.

## Aufgaben

### 1. `schema.sql` – Tabellen

Was gespeichert werden muss:

| Zweck | Inhalt | Woher |
|---|---|---|
| Dokumente | arXiv-ID, DOI, Titel, Abstract, Autoren, Erstveröffentlichung, Link, Quelle, Kategorien, Zeitschriftenverweis, Zeitpunkt des Abrufs | `Document` in `src/sources/sources.py` |
| Chunks | Verweis aufs Dokument, Position, Text | `Chunk` in `src/chunking/chunking.py` |
| Such-Cache | Welche Schlagwörter mit welchem Filter wann welche Dokumente geliefert haben | für „schon kürzlich geholt?“ |
| Messläufe | Zeitpunkt, Variante (ohne Tool / nur BM25 / hybrid), Schlagwörter, Frage, k, Input- und Output-Tokens, Dauer in ms, richtige Quelle gefunden ja/nein | KPI-Messung, Karte #6 |

Entscheidungen, die du treffen und begründen solltest:

- Autoren und Kategorien: Array-Spalte oder eigene Tabelle? Was heißt das für die Abfrage „alle Paper von Autor X“?
- Zwei arXiv-Einträge mit derselben DOI gibt es wirklich (1409.6928 und 1409.6919). Ist die DOI ein zweiter eindeutiger Schlüssel, oder dürfen beide gespeichert werden?
- Chunks hängen von `chunk_size` und `overlap` ab. Speicherst du die Parameter mit, oder werden Chunks bei geänderten Parametern neu erzeugt?
- Vektoren: speichern oder nicht? Dazu ist `pgvector` in ADR 0002 noch offen.

### 2. `upsert_document.sql`

Ein Dokument speichern; gibt es die ID schon, werden die Felder aktualisiert. Parameter: alle Felder aus Aufgabe 1.

### 3. `find_cached_search.sql`

Liefert die Dokument-IDs einer früheren Suche mit denselben Schlagwörtern und demselben Filter, aber nur, wenn sie jünger als `%(max_age)s` ist. Entschieden: 7 Tage (R13 in `Phase2/Pseudocode.md`). Dokumente und Embeddings selbst veralten nicht. Überleg, wie du die Schlagwörter vergleichbar machst (Reihenfolge, Groß-/Kleinschreibung).

### 4. `insert_run.sql`

Einen Messlauf speichern.

### 5. `kpi_by_variant.sql`

Pro Variante: Anzahl Läufe, durchschnittliche Input-Tokens, durchschnittliche Dauer, Trefferquote. Daraus wird das Delta „mit gegen ohne Tool“.

### 6. Optimierung

Eine Abfrage aus 3 oder 5 mit `EXPLAIN ANALYZE` messen, einen passenden Index anlegen, erneut messen und das Vorher-Nachher in einem kurzen ADR festhalten.

## Was danach in Python passiert (Claude)

Sobald `schema.sql`, `upsert_document.sql` und `find_cached_search.sql` stehen, kommt eine Quelle mit Cache: Erst fragt sie die Datenbank, nur wenn nichts Frisches da ist, arXiv. Mit `insert_run.sql` speichert die Evaluation ihre Messläufe.
