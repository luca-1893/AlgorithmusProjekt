# Schema-Entwurf

Entwurf für `sql/schema.sql`, bevor das SQL geschrieben wird. Die Begründungen stammen von Luca.

## Übersicht

```
documents ──1:n──▶ chunks
    │
    └──n:m──▶ Such-Cache (offen)

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
| chunk_size | integer | nein | | E9 |
| overlap | integer | nein | | E9 |
| fetched_at | timestamptz | nein | `DEFAULT` aktueller Zeitpunkt | Zeitpunkt mit Zeitzone, von der Datenbank gesetzt. |

## `chunks`

| Spalte | Typ | NULL? | Regel | Begründung |
|---|---|---|---|---|
| document_id | integer | nein | FK → `documents`, `ON DELETE CASCADE` | E10 |
| position | integer | nein | ab 0 | Reihenfolge im Dokument, wie `Chunk.position` in Python. |
| text | text | nein | | |
| | | | PRIMARY KEY `(document_id, position)` | |

## Such-Cache

*offen*

## `runs`

*offen*

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

## Offene Punkte

- Python liefert fehlende Werte als `""`; vor dem Speichern muss daraus `None` werden.
- Die ID vergibt Postgres; Python braucht sie für die Chunks zurück (`RETURNING`, bei `upsert_document.sql`).
- Vektoren: R16 in `Phase2/Pseudocode.md` will gespeicherte Vektoren je Chunk, Modell und Chunk-Parametern wiederverwenden. Wo und wie sie gespeichert werden, ist offen (ADR 0002, `pgvector`).
- R13 legt das Höchstalter des Such-Caches auf 7 Tage fest.
