# 15 Index und EXPLAIN ANALYZE

**In einem Satz:** Ein zusammengesetzter B-Baum-Index auf `searches (keywords, searched_at DESC)` macht die Cache-Abfrage gemessen etwa 140-mal schneller, und `EXPLAIN ANALYZE` zeigt, ob Postgres ihn nutzt.

## Kernidee

- **Ohne Index:** Seq Scan, Postgres liest jede Zeile; die Zeit wächst mit der Tabelle.
- **B-Baum-Index:** sortierte Struktur, Suche in O(log n); kann nur **führende Spalten** für Gleichheit nutzen.
- **Spaltenreihenfolge:** `keywords` vorn (Suche mit `=`), `searched_at DESC` dahinter (jüngste Suche zuerst, `ORDER BY searched_at DESC LIMIT 1` ohne Sortieren).
- **EXPLAIN** zeigt den geplanten Weg und geschätzte Kosten; **EXPLAIN ANALYZE** führt die Abfrage wirklich aus und misst die Zeit.
- **Preis:** Jeder Insert muss den Index mitpflegen.
- Primärschlüssel und UNIQUE bekommen automatisch einen Index.

## Ablauf (Messung ADR 0005)

```
50.001 Zeilen in searches (generate_series, 5.000 Schlagwort-Paare, 60 Tage)
ANALYZE searches;                       -- Statistik für den Planer
EXPLAIN ANALYZE <Unterabfrage aus find_cached_search.sql>;
CREATE INDEX IF NOT EXISTS searches_keywords_searched_at ON searches (keywords, searched_at DESC);
EXPLAIN ANALYZE <dieselbe Abfrage>;     -- alles in einer Transaktion, danach ROLLBACK
```

## Mini-Beispiel

| | ohne Index | mit Index |
|---|---|---|
| Plan | Seq Scan on searches | Index Scan using searches_keywords_searched_at |
| geschätzte Kosten | 1.993–3.269 | 8,45 |
| Execution Time | 3,33 / 3,75 / 3,96 ms | 0,026 / 0,027 / 0,024 ms |

Schreiben von 1.000 Zeilen: mit Index 2,9 / 4,7 / 4,5 ms, ohne 0,8 / 1,9 / 1,8 ms, also etwa 2–3 µs mehr pro Zeile; pro Tool-Aufruf entsteht höchstens eine neue Suche.

## Komplexität

Seq Scan O(n), Index Scan O(log n + Treffer). Insert mit Index zusätzlich O(log n).

## Im Projekt

- `sql/schema.sql`: `searches_keywords_searched_at` (ADR 0005) und ein **Hash-Index** `chunks_text` auf `chunks.text` für die Vektor-Wiederverwendung nach Text (C12): ein B-Baum hat eine Größengrenze pro Eintrag (etwa 2,7 kB), die ein Chunk aus 200 Wörtern überschreiten kann.
- Kein eigener Index nötig für `find_chunks`, `find_embeddings` und den äußeren Teil von `find_cached_search`: die Primärschlüssel decken die Bedingungen schon ab (führende Spalte passt).
- Voraussetzung: gleiche Normalisierung der Schlagwörter (`normalize_key`, E13), sonst findet `=` nichts.

## Typische Prüferfragen

- **Warum nicht `(searched_at, keywords)`?** Mit dem Bereich vorn grenzt der Index nur auf 7 Tage ein, nicht auf die Schlagwörter.
- **Warum kein GIN-Index?** GIN ist für „enthält“ (`@>`) gedacht; der Cache vergleicht ganze Arrays mit `=`.
- **Was ist der Unterschied zwischen EXPLAIN und EXPLAIN ANALYZE?** Plan mit Schätzung gegen echte Ausführung mit gemessener Zeit.
- **Warum stiegen die Seq-Scan-Kosten von Lauf zu Lauf?** Zurückgerollte Zeilen bleiben als tote Zeilen in der Tabelle, bis `VACUUM` läuft.

## Stolperfallen

- Kosten in EXPLAIN sind Schätzeinheiten des Planers, keine Millisekunden.
- Die Messung nutzt künstliche Daten; die Richtung des Ergebnisses hängt davon nicht ab, die genauen Zahlen schon.
