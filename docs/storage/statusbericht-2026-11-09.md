# Statusbericht SQL-Session (Person B: Messläufe und Lesen)

Stand: 09.11.2026, Branch `luca-dev`

## Fertig

- `sql/insert_run.sql`: speichert einen Messlauf und gibt die `id` zurück (`7769e7d`)
- `sql/update_run_found_source.sql`: bewertet einen Lauf über seine `id` (`a661c37`)
- `sql/kpi_by_variant.sql`: pro Variante Anzahl, Ø Input-Tokens, Ø Dauer und Trefferquote; bei unbewerteten Varianten `NULL` statt Division durch Null (`e8911a0`)
- `sql/find_chunks.sql`: Chunks zu einer Liste von Dokument-IDs, sortiert nach Dokument und Position (`4af8125`)
- `sql/find_embeddings.sql`: Vektoren zu Dokument-IDs und genau einem Modell (`9f2cb69`)
- `sql/insert_embedding.sql`: speichert einen Vektor; gibt es ihn schon, passiert nichts (`0d4f3a3`)
- Alle sechs Dateien sind mit psycopg und `load_sql` gegen `algorithmusprojekt_test` getestet, jeweils mit mindestens einem Fall, der scheitern soll.
- Lokales Setup unter Windows: PostgreSQL 18.6, beide Datenbanken, `schema.sql` eingespielt

## Offen

- Kreuz-Review: Luca prüft die 6 Dateien von Person B.
- Kreuz-Review: Person B prüft Lucas 5 Dateien: `upsert_document`, `insert_search`, `find_cached_search`, `delete_chunks`, `insert_chunks`.
- PyCharm-Verbindung unter Windows: `pgpass.conf` und `DATABASE_URL` müssen einmal in einer eigenen PowerShell außerhalb der Claude-App gesetzt werden (Windows leitet AppData-Zugriffe der App um).

## Parknotiz

- **Stand:** Alle Dateien von Person B sind fertig und auf `luca-dev` gepusht. Die Messläufe bis Sonntag sind damit SQL-seitig abgedeckt.
- **Erster Schritt nächstes Mal:** `git pull`, dann Lucas `upsert_document.sql` in der Test-DB mit eigenen Werten testen, inklusive eines Falls, der scheitern soll. Danach in zwei Sätzen erklären, was die Datei tut.

## Später-Liste

- Python: Nach `update_run_found_source` den `rowcount` prüfen. 0 heißt, die ID gab es nicht, und Postgres meldet dabei keinen Fehler.
- Python: `kpi_by_variant` liefert die Zahlen als `Decimal`, nicht als `float`.
- `hit_rate` eventuell mit `ROUND(…, 2)` runden, falls die Ausgabe zu lang ist.
- Aufgabe 6 (Optimierung): eine Abfrage mit `EXPLAIN ANALYZE` messen, einen Index anlegen, erneut messen und das Ergebnis als ADR festhalten.
- Test-DB aufräumen: Die Übungstabellen `ausleihe` und `buch` sowie die Beispielzeilen in `runs` werden nicht mehr gebraucht.
