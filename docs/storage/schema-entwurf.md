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
| *ID* | integer, IDENTITY | nein | PRIMARY KEY | |
| source | text | nein | `UNIQUE (source, source_id)` | |
| source_id | text | nein | ↑ | |
| doi | text | ja | nicht UNIQUE | |
| title | text | nein | | |
| abstract | text | ja | `NULL` statt `''` | |
| authors | text[] | nein | leeres Array statt `NULL` | |
| published | date | nein | | |
| url | text | nein | | |
| categories | text[] | nein | leeres Array statt `NULL` | |
| journal_ref | text | ja | `NULL` statt `''` | |
| origin | text | nein | `CHECK`: `html`, `pdf`, `abstract` | |
| full_text | text | ja | `NULL` genau dann, wenn `origin = 'abstract'` | |
| chunk_size | integer | nein | | |
| overlap | integer | nein | | |
| fetched_at | timestamptz | nein | `DEFAULT` aktueller Zeitpunkt | |

## `chunks`

| Spalte | Typ | NULL? | Regel | Begründung |
|---|---|---|---|---|
| document_id | integer | nein | FK → `documents`, `ON DELETE CASCADE` | |
| position | integer | nein | ab 0 | |
| text | text | nein | | |
| | | | PRIMARY KEY `(document_id, position)` | |

## Such-Cache

*offen*

## `runs`

*offen*

## Entscheidungen

| # | Entscheidung | Begründung |
|---|---|---|
| 1 | Künstliche ID als Primärschlüssel, eindeutig ist `(source, source_id)` | |
| 2 | `source_id` ohne Versionsnummer, nicht die URL | |
| 3 | DOI nicht UNIQUE, Duplikate per `GROUP BY … HAVING` | |
| 4 | Fehlende Werte als `NULL`, nicht als `''` | |
| 5 | Autoren und Kategorien als Array, keine eigene Tabelle | |
| 6 | Volltext speichern statt nur Chunks | |
| 7 | Herkunft des Texts speichern (`origin`) | |
| 8 | Dokumente ohne Volltext behalten (`origin = 'abstract'`) | |
| 9 | Chunk-Parameter am Dokument, `NOT NULL` | |
| 10 | Chunks werden mit ihrem Dokument gelöscht | |

## Offene Punkte

- Python liefert fehlende Werte als `""`; vor dem Speichern muss daraus `None` werden.
- Die ID vergibt Postgres; Python braucht sie für die Chunks zurück (`RETURNING`, bei `upsert_document.sql`).
- Vektoren: R16 in `Phase2/Pseudocode.md` will gespeicherte Vektoren je Chunk, Modell und Chunk-Parametern wiederverwenden. Wo und wie sie gespeichert werden, ist offen (ADR 0002, `pgvector`).
- R13 legt das Höchstalter des Such-Caches auf 7 Tage fest.
