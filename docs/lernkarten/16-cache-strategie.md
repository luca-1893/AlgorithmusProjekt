# 16 Cache-Strategie

**In einem Satz:** Ein Datenbank-Cache vor arXiv und Voyage beantwortet gleiche Suchen der letzten 7 Tage aus PostgreSQL und bettet bekannte Chunks nicht neu ein, ohne dass die Pipeline davon weiß.

## Kernidee

- **Decorator (C1):** `CachedSource` ist selbst eine `Source` und umhüllt `ArxivSource`; `CachedEmbedder` umhüllt `VoyageEmbedder`. Pipeline und arXiv-Quelle bleiben unverändert, für Messläufe lässt sich der Cache einfach weglassen.
- **Was veraltet:** nur das Suchergebnis (täglich neue Paper) → Höchstalter 7 Tage. Dokumente und Vektoren veralten nicht: gleicher Text + gleiches Modell = gleicher Vektor.
- **Schlüssel der Suche:** Schlagwörter und Kategorien kleingeschrieben und sortiert (`normalize_key`, E13), dazu Datumsgrenzen und `peer_reviewed_only`.
- **Fail open:** Datenbank weg → ohne Cache weiter, Hinweis „Cache nicht verfügbar“ (R15, C4, C5).
- Die Frage (`query`) wird nie gecacht (C11).

## Ablauf

```
CachedSource.search:
    ids = find_cached_search(schlagwörter, filter, 7 Tage)        R13
    WENN Anzahl(ids) >= max_treffer: "Dokumente aus dem Cache" → Dokumente aus DB    C2, C7
    sonst arXiv fragen (Fehler gehen an die Pipeline, C6)
    WENN leer: nicht speichern                                     C9
    Dokumente upserten; Chunks nur neu schreiben, wenn Texte sich änderten   R14, C10
    Suche mit Dokument-IDs in arXiv-Reihenfolge speichern
CachedEmbedder (nur "document"):
    gespeicherte Vektoren per Chunk-Text holen; nur fehlende einbetten und speichern   R16, C12, C13
```

## Mini-Beispiel

- `["UML", "BM25"]` und `["bm25", "uml"]` ergeben beide den Schlüssel `["bm25", "uml"]`.
- Einzelmessung laut Journal (15.11.2026): gleiche Anfrage 3,5 s ohne, 1,7 s mit Such-Cache; mit R16 erster Aufruf 22 Chunks an Voyage (2,3 s), zweiter nur die Frage (0,3 s).

## Im Projekt

- `src/cache/cache.py`, Pseudocode und Entscheidungen C1–C13: `docs/cache/cache-pseudocode.md`.
- `CACHE_MAX_AGE = timedelta(days=7)` in `src/storage/storage.py`; Abfrage `sql/find_cached_search.sql` (jüngste passende Suche, `searched_at >= now() - max_age`).
- Gespeichert wird `origin = 'abstract'` ohne Volltext (C8).
- Wichtige C-Entscheidungen: C2 Treffer nur mit mindestens `max_treffer` Dokumenten; C3 keine Existenzprüfung nötig (CASCADE); C9 leere Ergebnisse nicht speichern; C10 Chunks nur bei geänderten Texten neu schreiben, sonst löscht CASCADE die Vektoren; C12 Vektoren über den Chunk-Text finden (Hash-Index).
- Messläufe laufen bewusst **ohne** Cache, damit die Dauer die echte Recherche misst.

## Typische Prüferfragen

- **Warum 7 Tage?** Suchergebnisse veralten, weil täglich neue Paper erscheinen; Dokumente und Vektoren dagegen nicht. Das Höchstalter legt R13 fest; `searched_at` ist deshalb ein Zeitpunkt (`timestamptz`), kein Datum (E19).
- **Warum werden Chunks nicht bei jeder Suche neu gespeichert?** `save_chunks` löscht erst alle Chunks und per CASCADE ihre Vektoren; R16 wäre wirkungslos (C10).
- **Warum Vektoren über den Text statt über Dokument und Position?** Der Einbetter bekommt von der Pipeline nur Texte; gleiche Texte teilen sich einen Vektor (C12).
- **Was passiert, wenn eine Suche dauerhaft weniger als 20 Dokumente liefert?** Der Cache greift nach C2 nie, jede Wiederholung fragt arXiv neu.

## Stolperfallen

- Hinweise gelten für den **letzten** Aufruf einer Instanz; gleichzeitige Aufrufe könnten sie überschreiben (über stdio laufen Aufrufe nacheinander).
- Speichern und Nachschlagen müssen exakt dieselbe Normalisierung nutzen, sonst findet weder `=` noch der Index die Suche.
