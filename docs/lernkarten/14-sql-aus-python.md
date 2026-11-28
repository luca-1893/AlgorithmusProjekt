# 14 SQL-Abfragen aus Python

**In einem Satz:** `src/storage/storage.py` lädt je Zweck genau eine SQL-Datei aus `sql/`, führt sie mit psycopg 3 und benannten Parametern in einer Transaktion aus und übersetzt Datenbankfehler in `StorageError`.

## Kernidee

- **Eine Datei pro Zweck:** `load_sql("insert_chunks")` liest `sql/insert_chunks.sql`; SQL schreibt Luca selbst, Python führt es nur aus.
- **Benannte Parameter** `%(spalte)s` mit einem Dict; psycopg schickt die Werte getrennt vom SQL. Nie Strings zusammenkleben (Schutz vor SQL-Injection, richtige Typen).
- **Transaktion:** Jede Ausführung läuft in `connection.transaction()`; alles oder nichts. `save_chunks` löscht und fügt in **einer** Transaktion ein, damit ein Dokument nie ohne Chunks dasteht.
- **Fehler:** `psycopg.Error` → `StorageError`; der Aufrufer entscheidet (Cache: weiter ohne, R15).
- **Typen:** psycopg schickt Listen ohne Typ; Arrays ausdrücklich casten: `::text[]`, `::integer[]`, `::real[]`.
- **Leere Strings** aus Python werden vor dem Speichern zu `None` (`doi or None`).

## Ablauf

```
def execute(connection, name, params):
    sql = load_sql(name)
    try:
        with connection.transaction():
            return connection.execute(sql, params)
    except psycopg.Error as error:
        raise StorageError(f"{name}.sql failed: {error}")
```

## Mini-Beispiel

`sql/insert_chunks.sql`:

```
INSERT INTO chunks (document_id, position, text)
SELECT %(document_id)s, c.position - 1, c.text
FROM unnest(%(texts)s::text[]) WITH ORDINALITY AS c(text, position);
```

Abweichung 6.1: Ohne `::text[]` scheiterte `save_chunks(…, ["eins", "zwei", "drei"])` mit „function unnest(unknown) is not unique“; in DataGrip fiel es nicht auf, weil dort ein typisiertes Array-Literal stand. `WITH ORDINALITY` zählt ab 1, deshalb `position - 1`.

## Im Projekt

- psycopg 3.3.6; Verbindung über `DATABASE_URL` (Standard `postgresql:///algorithmusprojekt`), Tests gegen `algorithmusprojekt_test`, jeder Test in einer zurückgerollten Transaktion.
- `upsert_document.sql`: `INSERT … ON CONFLICT (source, source_id) DO UPDATE SET … = EXCLUDED.… RETURNING id` (R14: DOI kommt oft später dazu).
- `insert_embedding*.sql`: `ON CONFLICT … DO NOTHING` (vorhandener Vektor bleibt).
- `insert_search.sql`: CTE `WITH new AS (INSERT … RETURNING id)` plus `unnest(%(document_ids)s::integer[])`.
- `rate_run`: Ein `UPDATE` ohne Treffer ist in Postgres kein Fehler; `rowcount == 0` → `StorageError`.
- Lesend mit `row_factory=dict_row` (Zeilen als Dict).

## Typische Prüferfragen

- **Warum keine String-Verkettung?** SQL-Injection und Typfehler; Parameter werden vom Treiber sicher übergeben.
- **Warum zwei Dateien für das Ersetzen von Chunks?** Ein einzelnes Statement sähe beim Einfügen noch die alten Chunks; die gemeinsame Transaktion macht es trotzdem atomar.
- **Warum der Cast `::text[]`?** Postgres kennt mehrere `unnest`-Varianten und kann ohne Typ nicht wählen.
- **Was heißt RETURNING?** Das Statement gibt die vergebene ID gleich zurück; Python braucht sie für die Chunks.

## Stolperfallen

- SQL nicht nur in der IDE testen, sondern auch über den Weg, den das Programm nimmt (Lehre aus 6.1).
- Ein leeres Array ohne Typ lässt ebenfalls scheitern (C9, `insert_search.sql`).
- Reihenfolge nicht per `ORDER BY id` erzwingen, wenn sie von arXiv kommt; `find_documents` sortiert in Python.
