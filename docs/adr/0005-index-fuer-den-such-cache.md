# ADR 0005: Index für den Such-Cache

- **Status:** angenommen
- **Datum:** 2026-11-15
- **Entschieden von:** Luca (umgesetzt von Claude im Auftrag)

## Kontext

Bei jedem Tool-Aufruf fragt `find_cached_search.sql` zuerst, ob dieselbe Suche schon in den letzten 7 Tagen lief (R13). Die Unterabfrage sucht in `searches` nach `keywords` (Gleichheit) und `searched_at` (Bereich, jüngste zuerst). Auf diesen Spalten lag nur der Primärschlüssel `id`, also kein passender Index. `searches` wächst mit jeder Recherche und wird nie aufgeräumt.

Die übrigen Lese-Abfragen brauchen keinen eigenen Index:

| Abfrage | Bedingung | vorhandener Index |
|---|---|---|
| `find_cached_search`, äußerer Teil | `search_documents.search_id = …` | Primärschlüssel `(search_id, document_id)`, `search_id` steht vorn |
| `find_chunks` | `chunks.document_id = ANY(…)` | Primärschlüssel `(document_id, position)`, sortiert schon passend |
| `find_embeddings` | `document_id = ANY(…) AND model = …` | Primärschlüssel `(document_id, position, model)` |

## Messung

PostgreSQL 18.6 lokal, Datenbank `algorithmusprojekt_test`, 50.001 Zeilen in `searches`: 50.000 erzeugt mit `generate_series` (5.000 verschiedene Schlagwort-Paare, Zeitpunkte über 60 Tage verteilt) plus die gesuchte Zeile `['bm25', 'retrieval']`. Gemessen wurde die Unterabfrage aus `find_cached_search.sql` mit eingesetzten Werten, nach `ANALYZE searches`. Alles lief in einer Transaktion, die danach zurückgerollt wurde; drei Durchläufe.

| | ohne Index | mit Index |
|---|---|---|
| Plan | Seq Scan on searches | Index Scan using searches_keywords_searched_at |
| geschätzte Kosten | 1.993–3.269 | 8,45 |
| Execution Time | 3,33 / 3,75 / 3,96 ms | 0,026 / 0,027 / 0,024 ms |
| Faktor | | ≈ 140-mal schneller |

**Schreibkosten:** 1.000 neue Zeilen in `searches` einfügen

| | Durchlauf 1 | 2 | 3 |
|---|---|---|---|
| mit Index | 2,9 ms | 4,7 ms | 4,5 ms |
| ohne Index | 0,8 ms | 1,9 ms | 1,8 ms |

Die Kosten des Seq Scans steigen von Lauf zu Lauf, weil die zurückgerollten Zeilen als tote Zeilen in der Tabelle bleiben, bis `VACUUM` läuft. Das bestätigt nebenbei, dass ein Seq Scan mit der Tabellengröße wächst, der Index Scan nicht.

## Entscheidung

`schema.sql` bekommt:

```sql
CREATE INDEX IF NOT EXISTS searches_keywords_searched_at ON searches (keywords, searched_at DESC);
```

- **`keywords` vorn**, weil darauf mit `=` gesucht wird. Ein B-Baum kann nur die führenden Spalten für Gleichheit nutzen; mit `searched_at` vorn müsste er alle Suchen der letzten 7 Tage durchgehen.
- **`searched_at DESC` dahinter**, weil innerhalb gleicher Schlagwörter die jüngste Suche gesucht ist (`ORDER BY searched_at DESC LIMIT 1`). Der Index liefert sie als erste Zeile, ohne Sortieren.
- Die übrigen Filterspalten (Datumsgrenzen, Kategorien, `peer_reviewed_only`) bleiben außen vor: Nach `keywords` sind nur noch wenige Zeilen übrig, die Postgres direkt prüft.
- `IF NOT EXISTS`, damit `schema.sql` mehrfach ausführbar bleibt; zweimal hintereinander auf beiden lokalen Datenbanken geprüft.

## Betrachtete Alternativen

| Alternative | Warum nicht |
|---|---|
| kein Index | bei wenigen Suchen egal, wächst aber linear mit jeder Recherche; der Cache soll den Aufruf schneller machen, nicht langsamer |
| Index nur auf `keywords` | findet die Zeilen, muss sie aber noch nach `searched_at` sortieren; der zusammengesetzte Index spart das |
| `(searched_at, keywords)` | Bereich vorn: Der Index grenzt nur auf 7 Tage ein, nicht auf die Schlagwörter |
| GIN-Index auf `keywords` | für „enthält“-Abfragen (`@>`) gedacht; der Cache vergleicht ganze, normalisierte Arrays mit `=` |

## Konsequenzen

- Lesen: ≈ 0,03 ms statt mehrerer Millisekunden, unabhängig von der Größe der Tabelle.
- Schreiben: Jede neue Suche aktualisiert den Index mit; gemessen etwa 2–3 µs mehr pro Zeile. Pro Tool-Aufruf entsteht höchstens eine neue Suche, das fällt nicht ins Gewicht.
- Der Index setzt voraus, dass Python die Schlagwörter vor Speichern und Nachschlagen gleich normalisiert (`storage.normalize_key`, E13). Sonst finden `=` und Index die Suche nicht.
- Die Messung nutzt künstliche Daten; echte Schlagwörter sind ungleichmäßiger verteilt. Die Richtung des Ergebnisses hängt davon nicht ab.
