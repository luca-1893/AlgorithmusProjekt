# Pseudocode: storage

Python-Seite der Datenbank. Jede Funktion führt genau eine SQL-Datei aus `sql/` aus (Lucas Dateien, siehe `sql-aufgaben.md`) und übersetzt zwischen Python-Objekten und Tabellenzeilen. Alle schreibenden Funktionen laufen in einer Transaktion; Fehler der Datenbank werden zu `StorageError`.

```
FUNKTION normalisiere_schlüssel(werte)
    EINGABE:  werte – Liste von Schlagwörtern oder Kategorien
    AUSGABE:  dieselben Werte, kleingeschrieben und alphabetisch sortiert

    GIB sortiert(wert.casefold() FÜR JEDES wert IN werte) ZURÜCK
ENDE
// E13: Speichern (R14) und Nachschlagen (R13) müssen exakt dieselbe Normalisierung nutzen,
// sonst findet der Cache eine Suche nach ["UML", "BM25"] unter ["bm25", "uml"] nicht


FUNKTION leer_zu_null(text)
    WENN text leer: GIB LEER (NULL) ZURÜCK
    GIB text ZURÜCK
ENDE
// E-Entscheidung im Schema-Entwurf: fehlende Werte als NULL statt ''


FUNKTION speichere_dokument(verbindung, dokument, chunk_größe, überlappung, herkunft, volltext)
    EINGABE:  dokument – Document aus sources
              herkunft – 'abstract', 'html' oder 'pdf'; volltext LEER genau bei 'abstract'
    AUSGABE:  Datenbank-ID des Dokuments

    parameter ← Felder des Dokuments; doi und journal_ref über leer_zu_null
    id ← führe upsert_document.sql mit parameter aus, lies RETURNING id
    GIB id ZURÜCK
ENDE
// Gibt es (source, source_id) schon, werden die Felder aktualisiert (R14: DOI und
// Zeitschriftenverweis kommen oft später dazu); die ID bleibt gleich


FUNKTION finde_dokumente(verbindung, dokument_ids)
    AUSGABE:  Liste von gespeicherten Dokumenten (Document + Herkunft, Volltext, Chunk-Parameter)
              in der Reihenfolge von dokument_ids
    WENN dokument_ids leer: GIB leere Liste ZURÜCK
    zeilen ← Ergebnis von find_documents.sql als Wörterbuch id → zeile
    ergebnis ← leere Liste
    FÜR JEDE id IN dokument_ids:
        WENN id IN zeilen:
            ergebnis.anhängen(Dokument aus zeile, NULL bei doi, journal_ref, abstract → "")
    GIB ergebnis ZURÜCK
ENDE
// Die Reihenfolge kommt aus Python, nicht aus SQL: find_cached_search liefert die IDs in der
// Reihenfolge von arXiv, ein ORDER BY id würde sie zerstören. Unbekannte IDs fallen weg.


FUNKTION speichere_chunks(verbindung, dokument_id, texte)
    IN EINER TRANSAKTION:
        führe delete_chunks.sql aus      // alte Chunks und per CASCADE ihre Vektoren weg
        führe insert_chunks.sql mit texte aus
ENDE
// Zwei Dateien, weil ein Statement die alten Chunks beim Einfügen noch sieht;
// die Transaktion verhindert, dass ein Dokument zwischendurch ohne Chunks dasteht


FUNKTION finde_chunks(verbindung, dokument_ids)
    AUSGABE:  Liste von (dokument_id, position, text), sortiert nach Dokument und Position
    WENN dokument_ids leer: GIB leere Liste ZURÜCK
    GIB Ergebnis von find_chunks.sql ZURÜCK
ENDE


FUNKTION speichere_vektor(verbindung, dokument_id, position, modell, vektor)
    WENN vektor leer: FEHLER "Vektor ist leer"           // E31, sonst erst die Datenbank
    führe insert_embedding.sql aus                        // existiert er schon: nichts passiert
ENDE


FUNKTION finde_vektoren(verbindung, dokument_ids, modell)
    AUSGABE:  Wörterbuch (dokument_id, position) → Vektor
    WENN dokument_ids leer: GIB leeres Wörterbuch ZURÜCK
    GIB Ergebnis von find_embeddings.sql als Wörterbuch ZURÜCK
ENDE
// R16: Der Aufrufer bettet nur Chunks ein, die hier fehlen


FUNKTION speichere_suche(verbindung, schlagwörter, filter, dokument_ids)
    führe insert_search.sql mit normalisiere_schlüssel(schlagwörter),
          Filterfeldern (Kategorien normalisiert) und dokument_ids in Quell-Reihenfolge aus
ENDE


FUNKTION finde_gespeicherte_suche(verbindung, schlagwörter, filter, höchstalter = 7 Tage)
    AUSGABE:  Dokument-IDs der jüngsten passenden Suche in Quell-Reihenfolge,
              leere Liste, wenn keine passende Suche jünger als höchstalter ist
    GIB Ergebnis von find_cached_search.sql ZURÜCK
ENDE
// R13; leere Liste heißt: Quelle fragen


FUNKTION speichere_lauf(verbindung, lauf)
    AUSGABE:  ID des Laufs
    GIB RETURNING id von insert_run.sql ZURÜCK
ENDE


FUNKTION bewerte_lauf(verbindung, lauf_id, quelle_gefunden)
    anzahl ← betroffene Zeilen von update_run_found_source.sql
    WENN anzahl = 0: FEHLER "Lauf existiert nicht"
ENDE
// Postgres meldet bei einem UPDATE ohne Treffer keinen Fehler (Statusbericht, Später-Liste)


FUNKTION kennzahlen_je_variante(verbindung)
    AUSGABE:  Liste von Wörterbüchern {variant, runs, avg_input_tokens, avg_duration_ms, hit_rate}
    zeilen ← Ergebnis von kpi_by_variant.sql
    wandle Decimal in float um, hit_rate darf LEER bleiben (keine bewerteten Läufe)
    GIB zeilen ZURÜCK
ENDE
```

## Fehlerfälle

| Fall | Verhalten |
|---|---|
| Datenbank nicht erreichbar | `connect` wirft `StorageError`; die Pipeline macht ohne Cache weiter (R15) |
| SQL-Datei fehlt | `load_sql` wirft `StorageError` mit dem Dateinamen |
| Regel im Schema verletzt (z. B. leerer Chunk, ungültige Variante) | `StorageError` mit der Meldung von Postgres, die den Namen der Regel nennt; die Transaktion wird zurückgerollt |
| leerer Vektor | `ValueError` vor dem Datenbankaufruf |
| Bewertung eines unbekannten Laufs | `StorageError` |

## Bekannte Grenzen

- Die Chunk-Parameter stehen am Dokument; ob gespeicherte Chunks zu den aktuellen Parametern passen, prüft der Aufrufer.
