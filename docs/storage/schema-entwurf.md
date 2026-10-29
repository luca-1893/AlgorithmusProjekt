# Schema-Entwurf

Entwurf für `sql/schema.sql`, bevor das SQL geschrieben wird. Die Begründungen stammen von Luca.

## Übersicht

```
documents ──1:n──▶ chunks
    │
    └──n:m──▶ searches (über search_documents)

runs (Messläufe, unabhängig, offen)
```

## `documents`

Eine Zeile ist ein **Eintrag bei einer Quelle** (z. B. ein arXiv-Eintrag), keine veröffentlichte Arbeit.

| Spalte | Typ | NULL? | Regel | Begründung |
|---|---|---|---|---|
| *ID* | integer, IDENTITY | nein | PRIMARY KEY | E1 |
| source | text | nein | `UNIQUE (source, source_id)` | E1 |
| source_id | text | nein | ↑ | E1, E2 |
| doi | text | ja | nicht UNIQUE | E3, E4 |
| title | text | nein | | Jedes Paper hat einen Titel; er ist für Suche und Zitat zentral. |
| abstract | text | ja | `NULL` statt `''` | E4 |
| authors | text[] | nein | leeres Array statt `NULL` | E5 |
| published | date | nein | | Einträge ohne Datum übernimmt der Code nicht; der Zeitraumfilter braucht das Datum. |
| url | text | nein | | Einzige Referenz, die es zu jeder Quelle immer gibt. |
| categories | text[] | nein | leeres Array statt `NULL` | E5 |
| journal_ref | text | ja | `NULL` statt `''` | E4 |
| origin | text | nein | `CHECK`: `html`, `pdf`, `abstract` | E7, E8 |
| full_text | text | ja | `NULL` genau dann, wenn `origin = 'abstract'` | E6, E8 |
| chunk_size | integer | nein | `CHECK (chunk_size > 0)` | E9 |
| overlap | integer | nein | `CHECK (overlap >= 0 AND overlap < chunk_size)` | E9, E11 |
| fetched_at | timestamptz | nein | `DEFAULT` aktueller Zeitpunkt | Zeitpunkt mit Zeitzone, von der Datenbank gesetzt. |

## `chunks`

| Spalte | Typ | NULL? | Regel | Begründung |
|---|---|---|---|---|
| document_id | integer | nein | FK → `documents`, `ON DELETE CASCADE` | E10 |
| position | integer | nein | ab 0 | Reihenfolge im Dokument, wie `Chunk.position` in Python. |
| text | text | nein | | |
| | | | PRIMARY KEY `(document_id, position)` | |

## Such-Cache

Der Cache ersetzt nur den Aufruf der Quelle: Er merkt sich, welche Dokumente eine Suche geliefert hat. BM25 und Vektorsuche laufen danach bei jedem Aufruf neu.

### `searches`

Eine Zeile ist ein Aufruf der Quelle. Wiederholt sich eine Suche nach Ablauf des Höchstalters, entsteht eine neue Zeile.

| Spalte | Typ | NULL? | Regel | Begründung |
|---|---|---|---|---|
| *ID* | integer, IDENTITY | nein | PRIMARY KEY | wie `documents` |
| keywords | text[] | nein | normalisiert: kleingeschrieben, alphabetisch sortiert | E13 |
| published_from | date | ja | `NULL` = keine Untergrenze | E18 |
| published_to | date | ja | `NULL` = keine Obergrenze | E18 |
| categories | text[] | nein | leeres Array = kein Filter, sortiert | E13, E5 |
| peer_reviewed_only | boolean | nein | | Python liefert immer `True` oder `False`. |
| searched_at | timestamptz | nein | `DEFAULT` aktueller Zeitpunkt | E19 |

### `search_documents`

| Spalte | Typ | NULL? | Regel | Begründung |
|---|---|---|---|---|
| search_id | integer | nein | FK → `searches`, `ON DELETE CASCADE` | E15 |
| document_id | integer | nein | FK → `documents`, `ON DELETE CASCADE` | E16 |
| position | integer | nein | | E14 |
| | | | PRIMARY KEY `(search_id, document_id)` | |

## `runs`

Eine Zeile ist ein Messlauf: eine Testfrage, mit einer Variante beantwortet.

| Spalte | Typ | NULL? | Regel | Begründung |
|---|---|---|---|---|
| *ID* | integer, IDENTITY | nein | PRIMARY KEY | wie `documents` |
| run_at | *offen* | | | |
| variant | text | nein | `CHECK`: `agent_websearch`, `bm25`, `hybrid` | E20 |
| keywords | text[] | ja | `NULL` genau dann, wenn `variant = 'agent_websearch'` | E21 |
| question | text | nein | | E22 |
| k | integer | ja | `CHECK (k BETWEEN 1 AND 20)`, `NULL` genau dann, wenn `variant = 'agent_websearch'` | E21 |
| input_tokens | integer | nein | `CHECK (input_tokens >= 0)` | E23 |
| output_tokens | integer | nein | `CHECK (output_tokens >= 0)` | E23 |
| duration_ms | integer | nein | `CHECK (duration_ms >= 0)` | E23 |
| found_source | boolean | ja | `NULL` = noch nicht bewertet | E24 |

## Entscheidungen

| E | Entscheidung | Begründung |
|---|---|---|
| 1 | Künstliche ID als Primärschlüssel, eindeutig ist `(source, source_id)` | Modular: Kommt eine weitere Quelle dazu, kann sie dieselben IDs vergeben wie arXiv. |
| 2 | `source_id` ohne Versionsnummer, nicht die URL | `v1` und `v2` sind dasselbe Paper; die URL enthält die Version und ist zudem uneinheitlich (`http`/`https`). |
| 3 | DOI nicht UNIQUE, Duplikate per `GROUP BY … HAVING` | Eine Zeile ist ein Quell-Eintrag, kein Werk. Zwei Einträge mit derselben DOI gibt es wirklich (1409.6928, 1409.6919); erst speichern, dann per Abfrage deduplizieren. |
| 4 | Fehlende Werte als `NULL`, nicht als `''` | Eindeutiger zu filtern; `UNIQUE` ignoriert `NULL`, aber nicht `''`. |
| 5 | Autoren und Kategorien als Array, keine eigene Tabelle | arXiv liefert zu Autoren nur Namen (keine Uni, keine ORCID), zu Kategorien nur Kürzel; der Filter fragt nur „enthält?“. Leere Liste statt `NULL`, wie `()` in Python. |
| 6 | Volltext speichern statt nur Chunks | Wegen des Overlaps brauchen die Chunks rund 25 % mehr Platz als der Volltext (6.000 Wörter → 38 Chunks, 7.600 Wörter). Neu chunken geht ohne erneuten Download; nur ein Extraktorwechsel braucht ihn. |
| 7 | Herkunft des Texts speichern (`origin`) | Die Normalisierung verschieden kodierter PDFs wird ein Thema; die Herkunft hilft beim Auswerten und Debuggen. |
| 8 | Dokumente ohne Volltext behalten (`origin = 'abstract'`) | Robust: Titel und Abstract sind chunkbar, das Dokument bleibt find- und zitierbar, der Volltext lässt sich später nachholen. |
| 9 | Chunk-Parameter am Dokument, `NOT NULL` | Alle Chunks eines Dokuments teilen die Parameter, am Chunk wären sie redundant. Veraltete Chunks findet ein einfaches `WHERE`. Fehlen die Parameter, soll das Speichern scheitern. |
| 10 | Chunks werden mit ihrem Dokument gelöscht | Ein Chunk ohne sein Dokument ergibt keinen Sinn (`ON DELETE CASCADE`). |
| 11 | Chunk-Parameter auch in der Datenbank prüfen | Dieselbe Regel wie `split_into_chunks` als zweite Absicherung. `BETWEEN` scheidet aus, weil es `overlap = chunk_size` erlauben würde. |
| 12 | Such-Cache als m:n über `search_documents` | Eine Suche liefert viele Dokumente, ein Dokument kommt in vielen Suchen vor. |
| 13 | Schlagwörter in Python normalisieren (kleinschreiben, sortieren) | `normalize_keywords` behält Groß- und Kleinschreibung und Reihenfolge. Speichern (R14) und Nachschlagen (R13) müssen exakt dieselbe Normalisierung nutzen. |
| 14 | Reihenfolge der Quelle speichern, keinen BM25-Score | arXiv liefert nach Relevanz sortiert; das relevanteste Dokument steht vorn. Ein BM25-Score hängt an Anfrage, Chunk und Korpus, nicht an Suche und Dokument. |
| 15 | Alte Suchen löschen, Dokumente behalten | Suchen sind nach 7 Tagen veraltet (R13), ihre Zuordnungen gehen per `CASCADE` mit. Dokumente leben länger, weil andere Suchen sie liefern können. |
| 16 | Zuordnungen gehen mit dem Dokument | Ohne `CASCADE` würde der Fremdschlüssel das Löschen eines Dokuments blockieren, solange eine Suche darauf zeigt. |
| 17 | Wiederholte Suche als neue Zeile, ohne Verweis auf die alte | Neue Ergebnisse sind möglich. Gleiche Suchen erkennt man an gleichen, normalisierten Parametern; die alte Zeile wird ohnehin aufgeräumt (E15). |
| 18 | Fehlender Zeitraum als `NULL` | `None` im `SearchFilter` heißt „keine Grenze“. Beim Wiederfinden braucht der Vergleich `IS NOT DISTINCT FROM`, weil `NULL = NULL` nicht `true` ist. |
| 19 | `searched_at` als `timestamptz`, von der Datenbank gesetzt | Ein `date` ist für das Höchstalter zu ungenau (23:59 gegen 00:01). Gesetzt und verglichen wird mit derselben Uhr, der der Datenbank. |
| 20 | Drei Varianten: `agent_websearch`, `bm25`, `hybrid` | Verglichen wird das eigene Tool mit dem Standardweg eines Agenten, der selbst im Web recherchiert. `hybrid` statt `vector_search`, weil die Variante BM25, Vektorsuche und Rangfusion kombiniert. |
| 21 | Schlagwörter und `k` fehlen bei `agent_websearch` | Der Agent sucht selbst; eigene Schlagwörter und ein `k` gibt es nur mit dem Tool. |
| 22 | `question` immer gesetzt | Varianten sind nur über dieselbe Frage vergleichbar. |
| 23 | Tokens exakt, Dauer in Millisekunden, alles `integer` und nicht negativ | Gerundete Werte verwischen das Delta (z. B. 4.237 gegen 4.611 Tokens); ganze Sekunden würden BM25 (0,1 s) und hybrid (1,3 s) kaum trennen. `integer` reicht bis rund 2,1 Mrd., also für Hunderttausende Tokens und Stunden in ms. Dauer = vom Senden des Prompts bis zur Antwort des Agenten. |
| 24 | `found_source` darf `NULL` sein | Ein Lauf wird zuerst gespeichert und später bewertet; `NULL` heißt „noch nicht bewertet“. |

## Offene Punkte

- Python liefert fehlende Werte als `""`; vor dem Speichern muss daraus `None` werden.
- Die ID vergibt Postgres; Python braucht sie für die Chunks zurück (`RETURNING`, bei `upsert_document.sql`).
- Vektoren: R16 in `Phase2/Pseudocode.md` will gespeicherte Vektoren je Chunk, Modell und Chunk-Parametern wiederverwenden. Wo und wie sie gespeichert werden, ist offen (ADR 0002, `pgvector`).
- R13 legt das Höchstalter des Such-Caches auf 7 Tage fest.
