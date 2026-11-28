# 13 Relationales Schema

**In einem Satz:** Sechs Tabellen in PostgreSQL speichern Dokumente, Chunks, Vektoren, den Such-Cache und die Messläufe; Schlüssel, Fremdschlüssel und CHECK-Regeln sichern die Daten ab.

## Kernidee

- **Tabellen:** `documents` → 1:n `chunks` → 1:n `chunk_embeddings`; `documents` n:m `searches` über `search_documents`; `runs` unabhängig.
- **Primärschlüssel** = UNIQUE + NOT NULL. Künstliche ID (`GENERATED ALWAYS AS IDENTITY`) bei `documents`, `searches`, `runs`; fachlich eindeutig ist `UNIQUE (source, source_id)` (E1).
- **Zusammengesetzte Schlüssel:** `chunks (document_id, position)`, `chunk_embeddings (document_id, position, model)`, `search_documents (search_id, document_id)`.
- **Fremdschlüssel mit ON DELETE CASCADE:** Dokument weg → Chunks weg → Vektoren weg; Suche weg → Zuordnungen weg (E10, E15, E16, E27).
- **CHECK:** Wertelisten, Bereiche, „genau dann, wenn“-Regeln; benannt `<tabelle>_invalid_<regel>`.
- **NULL vs. leer:** Fehlender Text ist `NULL`, nicht `''` (E4); fehlende Listen sind `'{}'`, nicht `NULL` (E5).

## Beispiele aus `sql/schema.sql`

```
CONSTRAINT documents_invalid_origin    CHECK (origin IN ('html', 'pdf', 'abstract'))
CONSTRAINT documents_invalid_overlap   CHECK (overlap >= 0 AND overlap < chunk_size)
CONSTRAINT documents_invalid_full_text CHECK ((full_text IS NULL) = (origin = 'abstract'))
CONSTRAINT chunks_invalid_text         CHECK (text <> '')
CONSTRAINT runs_invalid_keywords       CHECK ((keywords IS NULL) = (variant = 'agent_websearch'))
FOREIGN KEY (document_id, position) REFERENCES chunks (document_id, position) ON DELETE CASCADE
```

## Mini-Beispiel

- `SELECT null = null;` → `NULL`, nicht `true`; richtig ist `IS NULL`. Der Cache vergleicht Datumsgrenzen deshalb mit `IS NOT DISTINCT FROM` (E18).
- `UNIQUE` behandelt zwei `NULL` als verschieden, zwei `''` aber als gleich; deshalb `NULL` für fehlende DOI.
- `BETWEEN 0 AND chunk_size` scheidet für den Overlap aus, weil es `overlap = chunk_size` erlauben würde (E11).

## Im Projekt

- `sql/schema.sql` mehrfach ausführbar (`IF NOT EXISTS`), Entwurf mit Begründungen E1–E32 in `docs/storage/schema-entwurf.md`, ER-Diagramm `docs/storage/schema.drawio`, Übungen `sql/uebungen/test_*.sql`.
- PostgreSQL statt SQLite (ADR 0002): Server-Betrieb, mehrere Zugriffe, DataGrip.
- Vektoren als `real[]`, nicht `pgvector` (E28); Länge wird nicht geprüft, weil sie vom Modell abhängt (E29), aber nicht leer (E31).
- Relevanz-Scores werden nie gespeichert, sie hängen von der Anfrage ab.

## Typische Prüferfragen

- **Warum künstliche ID statt arXiv-ID als Schlüssel?** Eine weitere Quelle könnte dieselben IDs vergeben; eindeutig ist erst `(source, source_id)`.
- **Warum ist die DOI nicht UNIQUE?** Eine Zeile ist ein Quell-Eintrag, kein Werk; 1409.6928 und 1409.6919 haben dieselbe DOI (E3).
- **Warum Autoren als Array statt eigener Tabelle?** arXiv liefert nur Namen, der Filter fragt nur „enthält?“ (E5).
- **Lässt ein CHECK NULL durch?** Ja: CHECK lehnt nur `false` ab, `NULL` ergibt „unbekannt“ und passiert (z. B. `k BETWEEN 1 AND 20` bei `k = NULL`); deshalb gibt es eigene Regeln für NULL.

## Stolperfallen

- `CREATE TABLE IF NOT EXISTS` übernimmt keine Änderungen an bestehenden Tabellen; dafür braucht es ein `DROP` in der Testdatenbank, nie in `schema.sql`.
- Tabellen mit `REFERENCES` erst nach der Tabelle anlegen, auf die sie zeigen.
- `NOT NULL` lässt `''` durch; deshalb zusätzlich `CHECK (text <> '')` (E30).
