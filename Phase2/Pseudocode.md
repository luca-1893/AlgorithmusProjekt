# Pseudocode: Recherche-Pipeline

Gesamtablauf des Algorithmus, passend zu `Phase2/Flowchart_RAG-Pipeline.drawio`. Die Regelnummern R1 bis R16 und die Schleifen S1 und S2 stehen auch an den Rauten im Flowchart. Den Pseudocode der einzelnen Funktionen gibt es pro Modul unter `docs/<modul>/<modul>-pseudocode.md`.

## Eingaben und Parameter

| Name | Bedeutung | Wert |
|---|---|---|
| `schlagwörter` | Fachbegriffe, die das Sprachmodell liefert | z. B. „UML“, „class diagram“ |
| `k` | Anzahl Abschnitte in der Antwort | 1 bis 20, Standard 5 |
| `frage` | ursprüngliche Frage des Nutzers, beliebige Sprache | optional |
| `suchfilter` | Zeitraum, Kategorien, nur begutachtet | optional |
| `max_dokumente` | wie viele Dokumente die Quelle höchstens liefert | 20 |
| `chunk_größe`, `überlappung` | Wörter pro Chunk, gemeinsame Wörter benachbarter Chunks | 200, 40 |
| `m` | Kandidaten aus der BM25-Vorauswahl | 50 |
| `k1`, `b` | BM25-Parameter: Sättigung, Längenbremse | 1,5, 0,75 |
| `k_rrf` | Glättung der Rangfusion | 60 |
| `λ` | MMR-Gewicht Relevanz gegen Vielfalt | 0,7 |
| `max_alter_suche` | wie lange ein Eintrag im Such-Cache gilt | 7 Tage |

## Startbedingung

Ein MCP-Client (z. B. Claude Code) ruft das Tool `research_papers` mit mindestens einem Schlagwort auf. Die Vektorsuche ist nur aktiv, wenn `VOYAGE_API_KEY` gesetzt ist; sonst arbeitet der Algorithmus nur mit BM25. Die Datenbank ist ebenfalls optional; ohne sie läuft jede Suche direkt gegen arXiv.

Die Cache-Regeln R13 bis R16 sind entworfen, die Umsetzung folgt, sobald die SQL-Dateien stehen (Karte #20).

## Endbedingungen

| Ende | Wann | Ausgabe |
|---|---|---|
| Erfolg | mindestens ein Abschnitt ausgewählt | bis zu k Abschnitte mit Quelle, als JSON |
| Keine Treffer | R4, R5 oder R7 greift | leere Liste mit Hinweis |
| Fehler | R1 oder R2 greift | Fehlermeldung an das Sprachmodell; der Server läuft weiter |

## Algorithmus

```
ALGORITHMUS Recherche(schlagwörter, k, frage, suchfilter)

    // R1: Eingabe prüfen
    WENN schlagwörter leer ODER k < 1 ODER k > 20:
        FEHLER "Ungültige Eingabe"                          → Ende: Fehler
    schlagwörter ← normalisiere_schlagwörter(schlagwörter)
    hinweise     ← leere Liste

    // R13, R15: erst im Cache nachsehen
    dokumente ← LEER
    VERSUCHE:
        dokumente ← cache.suche(schlagwörter, suchfilter, jünger als max_alter_suche)
    BEI Datenbank nicht erreichbar:
        hinweise.anhängen("Cache nicht verfügbar")      // weiter ohne Cache

    WENN dokumente LEER:
        // R2, R3: Dokumente von der Quelle holen
        VERSUCHE:
            dokumente ← quelle.suche(schlagwörter, max_dokumente, suchfilter)
        BEI Netzwerkfehler, Zeitüberschreitung oder ungültiger Antwort:
            FEHLER "Recherche-Quelle nicht erreichbar"      → Ende: Fehler
        // R14
        WENN Datenbank erreichbar:
            cache.speichere(schlagwörter, suchfilter, dokumente)

    // R4
    WENN dokumente leer:
        RÜCKGABE [], "Keine Treffer"                        → Ende: keine Treffer

    // S1: jedes Dokument in Chunks zerlegen
    chunks ← leere Liste
    FÜR JEDES dokument IN dokumente:
        text ← dokument.titel + Leerzeile + dokument.abstract
        FÜR JEDEN chunk IN erzeuge_chunks(dokument.id, text, chunk_größe, überlappung):
            chunks.anhängen((chunk, dokument))

    // R5
    WENN chunks leer:
        RÜCKGABE [], "Keine verwertbaren Quellen"           → Ende: keine Treffer

    // Keyword-Vorauswahl
    index, längen, N, avgdl ← baue_index(Texte aller chunks)
    bm25 ← top_m(schlagwörter, index, längen, N, avgdl, m, k1, b)

    // R6
    WENN kein Einbetter konfiguriert:
        RÜCKGABE nur_bm25(bm25, k, [])

    // R8: Kandidaten bestimmen
    WENN bm25 nicht leer:
        kandidaten ← Chunks aus bm25, in BM25-Reihenfolge
    SONST:
        kandidaten ← alle chunks                            // nur die Vektorsuche entscheidet

    // R9, R10: einbetten
    anfrage ← frage, WENN frage nicht leer, SONST schlagwörter verbunden
    VERSUCHE:
        anfrage_vektor      ← einbetten([anfrage], "query")
        // R16: nur Kandidaten ohne gespeicherten Vektor einbetten
        kandidaten_vektoren ← gespeicherte Vektoren (gleiches Modell, gleiche Chunk-Parameter),
                              fehlende per einbetten(…, "document") ergänzen und speichern
    BEI Einbettungsfehler:
        RÜCKGABE nur_bm25(bm25, k, ["Vektorsuche nicht verfügbar, nur BM25"])

    // Vektorsuche und Rangfusion (R12 bei Gleichstand)
    vektor_rangliste ← kandidaten absteigend nach cosinus(anfrage_vektor, kandidaten_vektor)
    fusion   ← reziproke_rang_fusion([BM25-Rangliste, vektor_rangliste], k_rrf)
    relevanz ← normalisiere_scores(Scores aus fusion)          // auf 0 bis 1

    // S2: Duplikat-Filter (MMR)
    auswahl ← leere Liste
    SOLANGE Kandidaten übrig UND Anzahl(auswahl) < k:
        bester ← Kandidat mit höchstem
                 λ · relevanz − (1 − λ) · höchste Ähnlichkeit zu einem Kandidaten in auswahl
        auswahl.anhängen(bester)
        bester aus den übrigen Kandidaten entfernen

    RÜCKGABE auswahl mit Quelle und Score, []               → Ende: Erfolg
ENDE


FUNKTION nur_bm25(bm25, k, hinweise)
    // R7
    WENN bm25 leer:
        RÜCKGABE [], hinweise + "Kein Chunk enthält ein Schlagwort"   → Ende: keine Treffer
    RÜCKGABE die ersten k aus bm25 mit BM25-Score, hinweise           → Ende: Erfolg
ENDE
```

## Entscheidungsregeln

| Regel | Bedingung | Folge |
|---|---|---|
| R1 | Schlagwörter leer oder k nicht zwischen 1 und 20 | Fehler „Ungültige Eingabe“, Ende |
| R2 | Quelle nicht erreichbar oder Antwort ungültig | Fehler „Recherche-Quelle nicht erreichbar“, Ende |
| R3 | Filter „nur begutachtet“ gesetzt | dreifach so viele Dokumente holen, Dokumente ohne Zeitschriftenverweis und ohne DOI verwerfen |
| R4 | Quelle liefert keine Dokumente | leere Liste, Hinweis „Keine Treffer“, Ende |
| R5 | aus den Dokumenten entsteht kein Chunk | leere Liste, Hinweis „Keine verwertbaren Quellen“, Ende |
| R6 | kein Einbetter konfiguriert (kein Schlüssel) | nur BM25 |
| R7 | nur BM25 und kein Chunk enthält ein Schlagwort | leere Liste, Hinweis „Kein Chunk enthält ein Schlagwort“, Ende |
| R8 | hybrid und BM25 findet Treffer | Kandidaten = BM25-Treffer; sonst alle Chunks |
| R9 | Frage vorhanden | Frage einbetten; sonst die Schlagwörter |
| R10 | Einbettung schlägt fehl (Schlüssel ungültig, Limit, Netz) | Hinweis setzen, weiter wie nur BM25 (R7) |
| R11 | Wort aus der Anfrage kommt in keinem Chunk vor | trägt nichts zum BM25-Score bei; leere Dokumente werden beim Indexaufbau übersprungen |
| R12 | Gleichstand bei Score oder Rang | kleinere Position bzw. kleinere Dok-ID zuerst |
| R13 | gleiche Suche (gleiche Schlagwörter, gleicher Filter) im Cache und jünger als 7 Tage | Dokumente aus der Datenbank, arXiv nicht fragen |
| R14 | Dokumente kamen von der Quelle | Dokumente und Suche in der Datenbank speichern; bekannte Dokumente aktualisieren (DOI und Zeitschriftenverweis kommen oft später dazu) |
| R15 | Datenbank nicht erreichbar | ohne Cache weiter, Hinweis „Cache nicht verfügbar“; die Recherche scheitert nicht daran |
| R16 | Vektor zu Chunk, Modell und Chunk-Parametern schon gespeichert | wiederverwenden statt neu einbetten |

R13 bis R16 sind entworfen, aber noch nicht umgesetzt; sie hängen an den SQL-Dateien.

## Schleifen

| Schleife | Läuft über | Endet, wenn |
|---|---|---|
| S1 | alle gefundenen Dokumente | jedes Dokument in Chunks zerlegt ist |
| S2 | Kandidaten nach Rangfusion | k Abschnitte gewählt sind oder keine Kandidaten mehr übrig sind |

Weitere Schleifen stecken in den Modulen: das Chunking, der Aufbau des invertierten Index, die BM25-Bewertung aller Kandidaten und Top-k per Heap. Sie stehen im jeweiligen Modul-Pseudocode.

## Komplexität

| Schritt | Laufzeit |
|---|---|
| Cache abfragen | eine Datenbankabfrage; bei Treffer entfällt der arXiv-Aufruf |
| Quelle abfragen | ein HTTP-Aufruf, dominiert vom Netzwerk |
| Chunking und Indexaufbau | O(T), T = Wörter aller Dokumente |
| BM25-Vorauswahl | O(P + C · \|q\| + C · log m), P = Postings der Anfragewörter, C = Kandidaten, \|q\| = Anfragewörter |
| Einbetten | zwei API-Aufrufe (Anfrage, Kandidaten); mit R16 nur für noch nicht gespeicherte Chunks |
| Vektorsuche | O(m · d), d = Vektorlänge (1024) |
| Rangfusion | O(m · log m) |
| MMR | O(k · m · d) |

## Annahmen und Vereinfachungen

- Nur Titel und Abstract, kein Volltext.
- Chunks werden in Wörtern gemessen, nicht in LLM-Tokens.
- Kein Token-Budget als Parameter; die Antwortgröße ist durch k und die Chunk-Größe begrenzt.
- Dokumente und Vektoren veralten nicht: Derselbe Text mit demselben Modell ergibt denselben Vektor. Veralten kann nur das Suchergebnis, weil täglich neue Paper erscheinen; deshalb gilt das Höchstalter von 7 Tagen nur für den Such-Cache.
- Relevanz (BM25-Score, Cosinus-Ähnlichkeit) wird nie gespeichert, weil sie von der Anfrage abhängt.
- arXiv ist englischsprachig; deutsche Schlagwörter finden kaum etwas, die Vektorsuche gleicht das nur für die Frage aus.
