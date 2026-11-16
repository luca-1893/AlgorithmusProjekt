# SQL-Cheatsheet

Alle Beispiele aus den Übungen, an einer Mini-Bibliothek und einem Einkaufszettel. Zum Ausprobieren in `algorithmusprojekt_test`.

## Werte schreiben

| Wert | Schreibweise | Beispiel |
|---|---|---|
| Text, Datum, Zeitpunkt | **mit** `'…'` | `'Faust'`, `'2024-05-14'`, `'2026-10-19 10:23:54+02'` |
| Zahl, `true`/`false`, `NULL` | **ohne** | `234`, `true`, `NULL` |

Ohne Anführungszeichen rechnet Postgres: `2024-05-14` ist 2005, `3-930685-28-0` ist −930710.

Schlüsselwörter dürfen klein oder groß geschrieben werden (`select` = `SELECT`).

## Typen

| Typ | Wofür |
|---|---|
| `text` | Zeichenketten jeder Länge |
| `integer` | ganze Zahlen bis rund 2,1 Milliarden |
| `boolean` | `true` / `false` |
| `date` | Datum ohne Uhrzeit |
| `timestamptz` | Zeitpunkt **mit** Zeitzone |
| `text[]`, `real[]` | Liste (Array) |

## Tabelle anlegen, einfügen, lesen

```sql
CREATE TABLE einkauf (
    artikel  text,
    menge    integer,
    gekauft  boolean
);

INSERT INTO einkauf (artikel, menge, gekauft)
VALUES ('Milch', 2, false),
       ('Brot', 1, true);

SELECT * FROM einkauf;
```

## Filtern, sortieren, begrenzen

```sql
SELECT * FROM buch WHERE ausgeliehen = false;
SELECT * FROM buch ORDER BY erschienen_am DESC;        -- neuestes zuerst (ASC = ältestes zuerst)
SELECT * FROM buch ORDER BY erschienen_am ASC LIMIT 1; -- nur das älteste
```

## NULL

```sql
SELECT * FROM buch WHERE seiten = NULL;    -- immer 0 Zeilen
SELECT * FROM buch WHERE seiten IS NULL;   -- richtig
SELECT null = null, null <> 5, null is null;   -- NULL, NULL, true
```

- `NULL` heißt „unbekannt“. Jeder Vergleich mit `NULL` ergibt wieder `NULL`.
- `WHERE` lässt nur `true` durch, `CHECK` lehnt nur `false` ab.
- `UNIQUE` behandelt zwei `NULL` als verschieden, `GROUP BY` steckt alle `NULL` in eine Gruppe.
- `IS NOT DISTINCT FROM` vergleicht wie `=`, behandelt aber `NULL` wie einen gleichen Wert.

## Schlüssel und Regeln

```sql
CREATE TABLE artikel (
    artikel_id  integer PRIMARY KEY,
    name        text NOT NULL UNIQUE,
    preis_cent  integer
);
```

- `PRIMARY KEY` = `UNIQUE` + `NOT NULL`.
- Für `PRIMARY KEY` und `UNIQUE` legt Postgres automatisch einen Index an.

### Künstliche ID und Eindeutigkeit über zwei Spalten

```sql
CREATE TABLE exemplar (
    exemplar_id  integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    bibliothek   text NOT NULL,
    signatur     text NOT NULL,
    titel        text NOT NULL,
    UNIQUE (bibliothek, signatur)
);

INSERT INTO exemplar (bibliothek, signatur, titel)
VALUES ('Stuttgart', 'A-17', 'Faust'),
       ('Berlin',    'A-17', 'Effi Briest');   -- ok: andere Kombination

INSERT INTO exemplar (bibliothek, signatur, titel)
VALUES ('Stuttgart', 'A-17', 'Doppelt');       -- Fehler: Kombination existiert
```

- `GENERATED ALWAYS AS IDENTITY`: Postgres zählt selbst hoch; beim `INSERT` die Spalte weglassen.
- Nummern sind eindeutig, aber **nicht lückenlos**: Ein gescheiterter Insert verbraucht seine Nummer. Zählen mit `COUNT(*)`, nicht mit der höchsten ID.

### CHECK

```sql
-- Werteliste
CREATE TABLE ausleihe2 (
    ausleihe_id  integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    status       text NOT NULL CHECK (status IN ('offen', 'zurück', 'verloren'))
);

-- Bereich und Vergleich zweier Spalten
CREATE TABLE ausleihe3 (
    ausleihe_id     integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ausgeliehen_am  date NOT NULL,
    zurueck_am      date,
    verlaengerungen integer NOT NULL DEFAULT 0 CHECK (verlaengerungen BETWEEN 0 AND 3),
    CHECK (zurueck_am IS NULL OR zurueck_am >= ausgeliehen_am)
);

-- „genau dann, wenn“: beide Seiten müssen gleich true oder gleich false sein
CREATE TABLE ausleihe4 (
    ausleihe_id  integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    status       text NOT NULL CHECK (status IN ('offen', 'zurück')),
    zurueck_am   date,
    CHECK ((zurueck_am IS NULL) = (status = 'offen'))
);
```

- Bedingungen über mehrere Spalten als eigene Zeile **am Ende** der Tabelle.
- `BETWEEN a AND b` schließt beide Grenzen ein.

### DEFAULT

```sql
erfasst_am  timestamptz NOT NULL DEFAULT now()
tags        text[] NOT NULL DEFAULT '{}'
```

`now()` liefert den Zeitpunkt mit Zeitzone; innerhalb einer Transaktion immer denselben (den Start der Transaktion).

## Fremdschlüssel

```sql
CREATE TABLE liste (
    liste_id  integer PRIMARY KEY,
    name      text NOT NULL
);

CREATE TABLE eintrag (
    eintrag_id  integer PRIMARY KEY,
    liste_id    integer NOT NULL REFERENCES liste(liste_id) ON DELETE CASCADE,
    artikel     text NOT NULL
);

INSERT INTO liste VALUES (1, 'Wocheneinkauf'), (2, 'Party');
INSERT INTO eintrag VALUES (1, 1, 'Milch'), (2, 1, 'Brot'), (3, 2, 'Chips');

DELETE FROM liste WHERE liste_id = 1;
SELECT * FROM eintrag;   -- nur noch 'Chips'
```

| Zusatz | Wird die Zeile gelöscht, auf die verwiesen wird … |
|---|---|
| *(nichts)* | Fehler, solange etwas darauf zeigt |
| `ON DELETE CASCADE` | verweisende Zeilen werden mitgelöscht |
| `ON DELETE SET NULL` | verweisende Spalte wird `NULL` (Spalte darf dann nicht `NOT NULL` sein) |

### Über zwei Spalten

```sql
CREATE TABLE buch_autor (
    buch_id   integer NOT NULL REFERENCES buch3(buch_id) ON DELETE CASCADE,
    position  integer NOT NULL,
    name      text NOT NULL,
    PRIMARY KEY (buch_id, position)
);

-- zeigt auf einen Primärschlüssel aus zwei Spalten
FOREIGN KEY (bibliothek, signatur) REFERENCES exemplar (bibliothek, signatur) ON DELETE CASCADE
```

## JOIN

```sql
SELECT l.name, e.artikel
FROM eintrag e
JOIN liste l ON e.liste_id = l.liste_id;        -- nur Zeilen mit Partner

SELECT l.name, e.artikel
FROM liste l
LEFT JOIN eintrag e ON e.liste_id = l.liste_id; -- alle Listen, ohne Partner steht NULL
```

- `e`, `l` sind Aliase; `tabelle.spalte` braucht man, wenn beide Tabellen gleich benannte Spalten haben.
- Bei `LEFT JOIN` bleiben alle Zeilen der Tabelle hinter `FROM`.

## Arrays

```sql
CREATE TABLE buch3 (
    buch_id  integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    titel    text NOT NULL,
    autoren  text[] NOT NULL DEFAULT '{}'
);

INSERT INTO buch3 (titel, autoren)
VALUES ('Good Omens', ARRAY['Terry Pratchett', 'Neil Gaiman']),
       ('Coraline',   ARRAY['Neil Gaiman']);

SELECT titel FROM buch3 WHERE 'Neil Gaiman' = ANY(autoren);   -- beide
SELECT titel, autoren[1] AS erstautor FROM buch3;             -- Index ab 1
```

## Mehrfach ausführbar

```sql
CREATE TABLE IF NOT EXISTS verlag (
    verlag_id  integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name       text NOT NULL UNIQUE
);
```

- Gibt es die Tabelle schon, passiert nichts, die Daten bleiben.
- **Änderungen** an einer bestehenden Tabelle kommen so nicht an; `CREATE TABLE` überschreibt nie.
- Tabellen mit `REFERENCES` erst nach der Tabelle anlegen, auf die sie zeigen.

## Gelernt

- Ein Statement mit mehreren Zeilen klappt ganz oder gar nicht (Atomarität).
- DataGrip bricht beim Ausführen mehrerer Statements nach dem ersten Fehler ab.
- `VALUES (…)` allein ist auch eine Abfrage; Spalten heißen dann `column1`, `column2` … und nichts wird gespeichert.

## Fehlercodes

| Code | Meldung | Bedeutung |
|---|---|---|
| 42804 | column … is of type date but expression is of type integer | Typ passt nicht, oft fehlende Anführungszeichen |
| 23505 | duplicate key value violates unique constraint | Wert (oder Kombination) gibt es schon |
| 23502 | null value in column … violates not-null constraint | Pflichtwert fehlt |
| 23503 | violates foreign key constraint | Verweis zeigt ins Leere, oder etwas zeigt noch auf die zu löschende Zeile |
| 23514 | violates check constraint | `CHECK`-Regel ergibt `false` |
| 42P07 | relation … already exists | Tabelle gibt es schon (`IF NOT EXISTS`) |

## DataGrip

| Was | Wie |
|---|---|
| Statement unter dem Cursor ausführen | ⌘ + Enter |
| nur Markiertes ausführen | markieren, ⌘ + Enter |
| Datei an Datenbank hängen | oben rechts im Editor Data Source und Schema wählen |
| ganze Datei ausführen | Rechtsklick auf die Datei → *Run* |
| aktuelle Datenbank prüfen | `SELECT current_database();` |
| Tabellen im Baum neu laden | ⌘ + R |
| DDL einer Tabelle ansehen | Rechtsklick → *SQL Scripts* → *Generate DDL* |
| Spaltentypen ansehen | Tabelle im Baum → *columns* aufklappen |
