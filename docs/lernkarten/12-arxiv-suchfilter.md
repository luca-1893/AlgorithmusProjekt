# 12 arXiv als Quelle und Suchfilter

**In einem Satz:** `ArxivSource` baut aus den Schlagwörtern eine Abfrage an die arXiv-API, liest den Atom-Feed in `Document`-Objekte und wendet Zeitraum, Kategorien und „nur begutachtet“ an.

## Kernidee

- **Warum arXiv:** offene API, keine Anmeldung, Open Access; Google Scholar hat keine offizielle API (A2).
- **Schlagwörter normalisieren:** Leerraum bereinigen, leere und doppelte (Groß/klein egal) entfernen, Reihenfolge bleibt.
- **Abfrage:** jedes Schlagwort als Phrase `all:"…"`, verbunden mit **OR** (mehr Treffer, die Feinauswahl macht BM25); sortiert nach Relevanz.
- **Filter:** Zeitraum und Kategorien filtert arXiv selbst; „nur begutachtet“ filtert das Programm danach (R3).
- **Begutachtet** heißt: Zeitschriftenverweis (`journal_ref`) oder DOI vorhanden.
- Dokument-ID ohne Versionsendung (`v1`, `v2` sind dasselbe Paper, E2).

## Ablauf

```
suche = all:"kw1" OR all:"kw2" ...                  (Anführungszeichen im Wort entfernt)
WENN kategorien: suche = (suche) AND (cat:a OR cat:b)
WENN ab/bis:     suche = suche AND submittedDate:[JJJJMMTT0000 TO JJJJMMTT2359]
                 fehlende Grenze: 1991-01-01 bzw. 9999-12-31
abrufen = max_treffer · 3, WENN nur_begutachtet, SONST max_treffer
URL: https://export.arxiv.org/api/query?search_query=…&start=0&max_results=…&sortBy=relevance&sortOrder=descending
```

## Mini-Beispiel

Schlagwörter `["UML", "class diagram"]` → `all:"UML" OR all:"class diagram"`. `published_after = "2024"` wird zu 2024-01-01 (`parse_date`). `peer_reviewed_only = true` bei 20 gewünschten Dokumenten: 60 abrufen, filtern, die ersten 20 zurückgeben. Duplikat-Fall: 1409.6928 und 1409.6919 tragen dieselbe DOI (E3).

## Komplexität

URL bauen O(L + K) (Länge der Schlagwörter und Kategorien); Feed lesen O(X), X = Länge der Antwort; Laufzeit dominiert ein HTTP-Aufruf.

## Im Projekt

- `src/sources/sources.py`: `normalize_keywords`, `SearchFilter`, `build_arxiv_url`, `parse_arxiv_feed`, `Source` (ABC), `ArxivSource`; `PEER_REVIEW_OVERFETCH = 3`.
- `max_documents = 20` (`PipelineConfig`). Netzwerk- und Formatfehler → `SourceError` (R2).
- Die Messläufe halten zwischen Tool-Läufen `ARXIV_PAUSE_S = 3.0` Sekunden Pause; arXiv drosselt trotzdem gelegentlich mit HTTP 429 (beobachtet bei 3,1 s Abstand, ADR 0004).
- Tests nutzen `FakeFetch` statt echter Anfragen.

## Typische Prüferfragen

- **Warum OR statt AND?** AND würde Dokumente verlieren, die nur einen Begriff enthalten; BM25 sortiert danach fein.
- **Warum dreimal so viele bei „nur begutachtet“?** Nach dem Filtern sollen noch genug Dokumente übrig bleiben.
- **Warum funktionieren deutsche Schlagwörter schlecht?** arXiv ist englischsprachig; „Klassendiagramm“ trifft nicht „class diagram“ (L4).
- **Warum ist Seitenzahl kein Filter?** arXiv nennt sie nur unregelmäßig im Kommentarfeld (L10).

## Stolperfallen

- Der Treffersatz ist schon nach den Schlagwörtern gefiltert; daraus folgt die IDF nahe null für das Hauptschlagwort (L2).
- Unvollständige Feed-Einträge (ohne ID, Titel oder Datum) werden still übersprungen.
