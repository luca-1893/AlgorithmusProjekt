# Pseudocode: cache

Eine Quelle, die vor eine andere Quelle geschaltet wird (meist arXiv) und die Cache-Regeln R13 bis R15 aus `Phase2/Pseudocode.md` umsetzt, und ein Einbetter, der vor Voyage geschaltet wird und R16 umsetzt. Für die Pipeline ist sie eine ganz normale `Source`; die Datenbank-Arbeit erledigen die Funktionen aus `storage`.

```
KLASSE CachedSource IST EINE Source
    innere_quelle  – die eigentliche Quelle, z. B. ArxivSource
    verbinde       – Funktion, die eine Datenbankverbindung öffnet (Standard: storage.connect)
    chunk_größe, überlappung – werden am Dokument gespeichert (Schema: documents)
    höchstalter    – wie alt eine gespeicherte Suche höchstens sein darf (7 Tage, R13)
    hinweise       – Hinweise des letzten Aufrufs, z. B. "Cache nicht verfügbar"
ENDE


FUNKTION CachedSource.suche(schlagwörter, max_treffer, filter)
    AUSGABE:  bis zu max_treffer Dokumente
    hinweise ← leere Liste
    filter   ← filter, sonst leerer Filter

    // R13, R15: erst im Cache nachsehen
    VERSUCHE:
        MIT verbinde() ALS verbindung:
            ids ← storage.finde_gespeicherte_suche(verbindung, schlagwörter, filter, höchstalter)
            WENN Anzahl(ids) ≥ max_treffer:
                hinweise.anhängen("Dokumente aus dem Cache")
                GIB storage.finde_dokumente(verbindung, erste max_treffer ids) ZURÜCK
    BEI StorageError:
        hinweise.anhängen("Cache nicht verfügbar")
        GIB innere_quelle.suche(schlagwörter, max_treffer, filter) ZURÜCK   // ohne Speichern

    // R2, R3: Quelle fragen; ihr Fehler geht unverändert an die Pipeline
    dokumente ← innere_quelle.suche(schlagwörter, max_treffer, filter)
    WENN dokumente leer: GIB dokumente ZURÜCK            // C9: leere Ergebnisse nicht speichern

    // R14: speichern, Fehler dabei kosten nur den Cache, nicht die Recherche
    VERSUCHE:
        MIT verbinde() ALS verbindung:
            FÜR JEDES dokument IN dokumente:
                id    ← storage.speichere_dokument(verbindung, dokument, chunk_größe, überlappung)
                texte ← Texte von erzeuge_chunks(dokument.id, dokument.text, chunk_größe, überlappung)
                WENN gespeicherte Chunk-Texte von id ≠ texte:      // C10
                    storage.speichere_chunks(verbindung, id, texte)
            storage.speichere_suche(verbindung, schlagwörter, filter, ids)
    BEI StorageError:
        hinweise.anhängen("Cache nicht verfügbar")

    GIB dokumente ZURÜCK
ENDE
```

## R16: Vektoren wiederverwenden

```
KLASSE CachedEmbedder IST EIN Embedder
    innerer_einbetter – der eigentliche Einbetter, z. B. VoyageEmbedder
    modell            – Name des Modells; Vektoren verschiedener Modelle passen nicht zusammen
    verbinde          – wie bei CachedSource
    hinweise          – Hinweise des letzten Aufrufs
ENDE


FUNKTION CachedEmbedder.anbieter_anfrage(texte, art)
    hinweise ← leere Liste
    WENN art = "query":
        GIB innerer_einbetter.einbetten(texte, "query") ZURÜCK          // C11

    VERSUCHE:
        MIT verbinde() ALS verbindung:
            gespeichert ← find_embeddings_by_text.sql(texte, modell)    // Text → Vektor
    BEI StorageError:
        hinweise.anhängen("Cache nicht verfügbar")
        GIB innerer_einbetter.einbetten(texte, "document") ZURÜCK

    fehlend ← Texte aus texte, die nicht in gespeichert sind, ohne Doppelte, in Reihenfolge
    neu ← innerer_einbetter.einbetten(fehlend, "document")
    FÜR JEDES (text, vektor) IN fehlend, neu:
        gespeichert[text] ← vektor

    VERSUCHE:
        MIT verbinde() ALS verbindung:
            FÜR JEDES (text, vektor) IN fehlend, neu:
                insert_embedding_by_text.sql(text, modell, vektor)       // für alle Chunks mit diesem Text
    BEI StorageError:
        hinweise.anhängen("Cache nicht verfügbar")

    GIB gespeichert[text] FÜR JEDEN text IN texte ZURÜCK
ENDE
```

## Entscheidungen

| Nr. | Entscheidung | Begründung |
|---|---|---|
| C1 | Cache als eigene Quelle vor der eigentlichen Quelle (Decorator) | Pipeline und arXiv-Quelle bleiben unverändert; der Cache lässt sich für Messläufe einfach weglassen (Entscheidung „kein Cache in Messläufen“, `docs/evaluation/leitfragen.md`) |
| C2 | Treffer nur, wenn die gespeicherte Suche **mindestens max_treffer** Dokumente hat | `max_treffer` gehört nicht zum Schlüssel der Suche. Hat eine frühere Suche nur 20 Dokumente geholt und jetzt werden 50 verlangt, wäre das Ergebnis zu klein; dann wird arXiv neu gefragt und die neue Suche gespeichert. |
| C3 | Keine Prüfung, ob die gespeicherten IDs noch in `documents` stehen | Kann nicht vorkommen: Löscht man ein Dokument, löscht `ON DELETE CASCADE` auch seine Zeilen in `search_documents`; `find_cached_search` liefert dann nur noch vorhandene IDs, und C2 greift. |
| C4 | Fehler der Datenbank beim Nachsehen: weiter mit der Quelle, ohne zu speichern | R15; bei einer kaputten Verbindung würde Speichern ohnehin scheitern. |
| C5 | Fehler der Datenbank beim Speichern: Dokumente trotzdem zurückgeben | Die Recherche ist schon gelungen; der Cache ist nur eine Beschleunigung. |
| C6 | Fehler der Quelle werden nicht abgefangen | Die Pipeline und der MCP-Server haben dafür schon einen Fehlerpfad (`SourceError`). |
| C7 | Hinweis „Dokumente aus dem Cache“ bei einem Treffer | Nachvollziehbar für Nutzer und Sprachmodell, warum die Antwort schneller kam und wie alt die Suche sein kann. |
| C9 | Leere Ergebnisse werden nicht gespeichert | Sonst lieferte der Cache 7 Tage lang „keine Treffer“, obwohl täglich neue Paper erscheinen. Aufgefallen beim Test: Eine leere ID-Liste hatte ohne Typ `insert_search.sql` scheitern lassen (wie bei `insert_chunks.sql`); die Datei wandelt den Parameter jetzt ausdrücklich in `integer[]` um. |
| C10 | Chunks nur neu speichern, wenn sich ihre Texte geändert haben | `save_chunks` löscht erst alle Chunks des Dokuments und per `CASCADE` ihre Vektoren. Würde jede neue Suche, die ein bekanntes Dokument enthält, die Chunks neu schreiben, gingen die gespeicherten Vektoren jedes Mal verloren. |
| C11 | Die Frage (`query`) wird nie gecacht | Sie ist fast jedes Mal anders, und Voyage bettet Fragen anders ein als Dokumente; im Schema hängen Vektoren außerdem an Chunks. |
| C12 | Vektoren werden über den **Chunk-Text** gefunden, nicht über Dokument und Position | Der Einbetter bekommt von der Pipeline nur Texte. So bleibt die Pipeline unverändert, und gleiche Texte in verschiedenen Dokumenten (z. B. zwei Fassungen eines Papers) teilen sich einen Vektor. Damit die Suche nach Text schnell bleibt, hat `chunks.text` einen Hash-Index: ein B-Baum hat eine Größengrenze pro Eintrag (etwa 2,7 kB), die ein Chunk aus 200 Wörtern überschreiten kann. |
| C13 | Neue Vektoren gelten für alle Chunks mit demselben Text | `insert_embedding_by_text.sql` speichert den Vektor zu jedem passenden Chunk; ein Text ohne gespeicherten Chunk (Datenbank fiel beim Speichern aus) wird nur zurückgegeben, nicht gespeichert. |
| C8 | Gespeichert wird `origin = 'abstract'` ohne Volltext | Die Pipeline arbeitet noch mit Titel und Abstract (ADR 0004). |

## Weitergabe der Hinweise

`Source` und `Embedder` bekommen ein Attribut `notes` (Standard: leer). Die Pipeline hängt die Hinweise der Quelle und des Einbetters an ihre eigenen an; damit erscheinen sie in `warnings` der Tool-Antwort.

## Bekannte Grenzen

- Gespeicherte Vektoren werden nicht nach den Chunk-Parametern unterschieden; das ist auch nicht nötig, weil gleicher Text gleichen Vektor ergibt.
- Die Frage selbst kostet weiterhin einen Voyage-Aufruf pro Recherche.
- Eine Instanz merkt sich die Hinweise des **letzten** Aufrufs; laufen zwei Aufrufe gleichzeitig auf derselben Instanz, können sie sich die Hinweise überschreiben. Der MCP-Server über stdio bearbeitet Aufrufe nacheinander.
- Liefert die Quelle für eine Suche dauerhaft weniger als `max_treffer` Dokumente (seltene Schlagwörter), greift der Cache nach C2 nie; jede Wiederholung fragt die Quelle erneut.
- Jeder Aufruf öffnet bis zu zwei Verbindungen; bei einem lokalen PostgreSQL sind das wenige Millisekunden.
