# Testdokumentation

Phase 4 des Hackathons (Karte #15). Stand: 15.11.2026 (abends), Branch `luca-dev`.

**Pflicht laut Vorgabe:** mindestens drei Testkategorien (Normalfall, Randfall, Fehlerfall), jeweils Input → erwartetes Output → tatsächliches Output, dazu eine Abweichungsanalyse. Optional: Laufzeitmessung und Vergleich mit Alternativen.

**Wo was steht**
- Diese Datei: Vorgehen, Übersicht, Coverage, ausgewählte Fälle im Detail, Abweichungsanalyse
- `Phase4/Testkatalog.md`: **alle** 325 Unittests mit Kategorie, Input → erwartet und tatsächlichem Ergebnis, automatisch erzeugt
- `Phase4/Klicktest-runs.md`: Anleitung, um das Schreiben der Messläufe in `runs` von Hand zu prüfen (Probelauf ohne API)
- Testcode: `src/<modul>/test_<modul>.py`

## 1. Vorgehen

- **Testfälle vor Code** (Hackathon-Regel 2): Pro Funktion erst Pseudocode, dann Unittests, die zunächst rot sind, dann die Implementierung, bis sie grün sind. In der Git-Historie sichtbar an Commits wie `test(bm25): … (red until top_m exists)`.
- **Werkzeug:** `unittest` aus der Standardbibliothek, Coverage mit `coverage` (Zeilen und Verzweigungen).
- **Externe Dienste** (arXiv, Voyage) werden in den Tests durch Attrappen ersetzt (`FakeFetch`, `FakePost`, `FakeSource`, `TopicEmbedder`). Die Tests laufen dadurch ohne Netz, ohne Schlüssel und immer gleich.
- **Datenbank:** Die Tests für `storage` laufen gegen `algorithmusprojekt_test`, jeder in einer Transaktion, die am Ende zurückgerollt wird. Ist die Datenbank nicht erreichbar, werden sie übersprungen statt rot.

**Ausführen** (aus dem Repo-Root):

```
.venv/bin/python -m unittest discover -s src -t src
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/coverage run --branch --source=src -m unittest discover -s src -t src
.venv/bin/coverage report --omit='*/test_*.py,*/__init__.py' -m
.venv/bin/python Phase4/testkatalog.py
```

## 2. Kategorien

| Kategorie | Bedeutung | Beispiel |
|---|---|---|
| **Normalfall** | typische, gültige Eingabe; das Ergebnis ist von Hand nachgerechnet | BM25-Score für „apfel milch“ |
| **Randfall** | gültige Eingabe an einer Grenze: leer, genau eins, Gleichstand, Sonderzeichen, Werte am Rand des erlaubten Bereichs | leerer Text, Chunk kürzer als `chunk_size`, Nullvektor |
| **Fehlerfall** | ungültige Eingabe oder ausfallender Dienst; erwartet ist ein eigener, verständlicher Fehler oder ein geregelter Ausweichweg | Overlap ≥ Chunk-Größe, arXiv nicht erreichbar, Voyage fällt aus |

Die Zuordnung im Katalog macht `testkatalog.py`: Fehlerfall, wenn der Test einen Fehler erwartet (`assertRaises`) oder einen ausfallenden Dienst simuliert; Randfall nach Stichwörtern im Testnamen (`empty`, `zero`, `only_`, `ties`, …); sonst Normalfall. Vier Tests sind von Hand umsortiert (`OVERRIDES` im Skript).

## 3. Übersicht

| Modul | Normalfall | Randfall | Fehlerfall | gesamt | wie erwartet |
|---|---|---|---|---|---|
| `sources` | 24 | 15 | 11 | 50 | 50 |
| `chunking` | 6 | 10 | 8 | 24 | 24 |
| `bm25` | 13 | 38 | 0 | 51 | 51 |
| `vector_search` | 19 | 17 | 17 | 53 | 53 |
| `ranking` | 7 | 9 | 1 | 17 | 17 |
| `pipeline` | 14 | 9 | 4 | 27 | 27 |
| `mcp_server` | 11 | 1 | 7 | 19 | 19 |
| `storage` | 13 | 16 | 9 | 38 | 38 |
| `cache` | 14 | 5 | 5 | 24 | 24 |
| `evaluation` | 14 | 5 | 3 | 22 | 22 |
| **gesamt** | **135** | **125** | **65** | **325** | **325** |

Alle Tests laufen wie erwartet. Die 5 Abweichungen in `storage` vom 14./15.11. sind behoben (Abschnitt 6.1).

## 4. Coverage

Gemessen mit `coverage 7.17.3`, Zeilen und Verzweigungen, ohne Testdateien.

| Modul | Anweisungen | nicht ausgeführt | Verzweigungen | Coverage | nicht abgedeckt |
|---|---|---|---|---|---|
| `bm25` | 55 | 0 | 20 | **100 %** | – |
| `chunking` | 22 | 0 | 8 | **100 %** | – |
| `ranking` | 15 | 0 | 10 | **100 %** | – |
| `pipeline` | 73 | 0 | 16 | **100 %** | – |
| `cache` | 82 | 0 | 14 | **100 %** | – |
| `sources` | 110 | 3 | 26 | 97 % | `http_get`: der echte Netzwerkaufruf |
| `vector_search` | 90 | 3 | 30 | 98 % | `http_post_json`: der echte Netzwerkaufruf |
| `storage` | 107 | 5 | 16 | 95 % | Fehlerzweige von `find_documents` und `kpi_by_variant` (Datenbankfehler mitten in einer Leseabfrage), leere ID-Liste bei `find_embeddings` |
| `evaluation` | 130 | 2 | 26 | 97 % | Pause zwischen echten arXiv-Anfragen und `if __name__ == "__main__"` |
| `mcp_server` | 53 | 9 | 8 | 82 % | `main()`: Start des Servers über die Kommandozeile |
| **gesamt** | **737** | **22** | **174** | **97 %** | |

**Bewertung:** Die Algorithmus-Module (`bm25`, `chunking`, `ranking`, `pipeline`) und der Cache sind vollständig abgedeckt. Offen sind nur Zeilen, die echte Netzwerkaufrufe machen oder den Server starten. Sie sind absichtlich durch Attrappen ersetzt und wurden stattdessen im Notebook und in den Messungen live ausgeführt.

## 5. Ausgewählte Fälle

Das tatsächliche Output wurde am 15.11.2026 live berechnet, nicht aus dem Test abgeschrieben.

### 5.1 Normalfall

| Nr. | Funktion | Input | erwartetes Output | tatsächliches Output | |
|---|---|---|---|---|---|
| N1 | `bm25.tokenize` | `"DEr  Apfel-Baum ist grün."` | `["der", "apfelbaum", "ist", "grün"]` | `["der", "apfelbaum", "ist", "grün"]` | ✓ |
| N2 | `chunking.split_into_chunks` | `"w1 … w10"`, `chunk_size=4`, `overlap=1` | `["w1 w2 w3 w4", "w4 w5 w6 w7", "w7 w8 w9 w10"]` | identisch | ✓ |
| N3 | `bm25.top_m` | Korpus aus 4 Mini-Dokumenten, Anfrage „apfel milch“, `m=2` | Dok 3 (0,767) vor Dok 0 (0,694), Referenzwerte aus `test_top_m_reference_m2` | `[(3, 0.767), (0, 0.694)]` | ✓ |
| N4 | `vector_search.cosine_similarity` | `(1, 2, 2)` und `(2, 0, 1)` | 4 / (3 · √5) ≈ 0,596 | `0.596` | ✓ |
| N5 | `ranking.reciprocal_rank_fusion` | Rankings `[1, 2]` und `[2, 3]`, `k_rrf=0` | 2 vor 1 vor 3; Score von 2 = 1/2 + 1/1 = 1,5 | `[(2, 1.5), (1, 1.0), (3, 0.5)]` | ✓ |
| N6 | `pipeline.research` (nur BM25) | Schlagwort „uml“, `k=2`, Dokumente zu UML-Klassen, neuronalen Netzen, UML-Sequenzen | die zwei UML-Dokumente, das Netz-Dokument nicht | `UML class diagrams` (0,618), `UML sequence diagrams` (0,462) | ✓ |
| N7 | `pipeline.research` (hybrid) | wie N6, mit Einbetter und Frage „UML class“ | die zwei UML-Dokumente | `UML class diagrams`, `UML sequence diagrams` | ✓ |

### 5.2 Randfall

| Nr. | Funktion | Input | erwartetes Output | tatsächliches Output | |
|---|---|---|---|---|---|
| R1 | `bm25.tokenize` | `""` | `[]` | `[]` | ✓ |
| R2 | `bm25.tokenize` | `"COVID-19 E-Mail don’t Straße"` | `["covid19", "email", "dont", "strasse"]` | identisch | ✓ |
| R3 | `chunking.split_into_chunks` | `"w1 w2"`, `chunk_size=4`, `overlap=1` (kürzer als ein Chunk) | ein Chunk `["w1 w2"]` | `["w1 w2"]` | ✓ |
| R4 | `bm25.top_m` | Anfrage „pizza“, kein Dokument enthält das Wort | `[]` | `[]` | ✓ |
| R5 | `vector_search.cosine_similarity` | Nullvektor `(0, 0)` und `(1, 2)` | `0.0` statt Division durch null | `0.0` | ✓ |
| R6 | `vector_search.mmr_select` | Relevanz `[1.0, 0.95, 0.6]`, Vektor 1 fast gleich Vektor 0, `k=2`, `λ=0,5` | `[0, 2]`: das Fast-Duplikat wird übersprungen | `[0, 2]` | ✓ |
| R7 | `ranking.normalize_scores` | `[0.3, 0.3]` (alle gleich) | `[1.0, 1.0]` statt Division durch null | `[1.0, 1.0]` | ✓ |
| R8 | `pipeline.research` | Quelle liefert keine Dokumente | keine Treffer, Hinweis „Keine Treffer“ | `((), ("Keine Treffer",))` | ✓ |

### 5.3 Fehlerfall

| Nr. | Funktion | Input | erwartetes Output | tatsächliches Output | |
|---|---|---|---|---|---|
| F1 | `chunking.split_into_chunks` | `overlap=4` bei `chunk_size=4` (Endlosschleife droht) | `ValueError` | `ValueError: chunk_size must be > 0 and 0 <= overlap < chunk_size` | ✓ |
| F2 | `sources.build_arxiv_url` | keine Schlagwörter | `ValueError` | `ValueError: keywords must not be empty` | ✓ |
| F3 | `sources.parse_arxiv_feed` | kaputtes XML `"<feed><entry>"` | `SourceError` | `SourceError: arXiv response is not valid XML: no element found: …` | ✓ |
| F4 | `ArxivSource.search` | Netzwerk nicht erreichbar | `SourceError` | `SourceError: arXiv is not reachable: <urlopen error no route>` | ✓ |
| F5 | `pipeline.research` (hybrid) | Einbetter wirft `EmbeddingError` | kein Absturz; Ergebnis aus BM25, Hinweis „Vektorsuche nicht verfügbar, nur BM25“ (R10) | Dokumente 1 und 3, `("Vektorsuche nicht verfügbar, nur BM25",)` | ✓ |
| F6 | `VoyageEmbedder()` | `VOYAGE_API_KEY` nicht gesetzt | `EmbeddingError` beim Anlegen, nicht erst beim ersten Aufruf | `EmbeddingError: VOYAGE_API_KEY is not set` | ✓ |
| F7 | `pipeline.research` | Schlagwörter `["  ", ""]` | `ValueError`, arXiv wird nicht gefragt | `ValueError: keywords must not be empty` | ✓ |
| F8 | `vector_search.mmr_select` | `λ = 1,5` (außerhalb 0…1) | `ValueError` | `ValueError: k must be > 0 and lambda_ between 0 and 1` | ✓ |

## 6. Abweichungsanalyse

### 6.1 Behoben: `insert_chunks.sql` aus Python

| | |
|---|---|
| **Input** | `save_chunks(verbindung, dokument_id, ["eins", "zwei", "drei"])` |
| **erwartet** | drei Zeilen in `chunks`, Positionen 0 bis 2 |
| **tatsächlich** | `StorageError: insert_chunks.sql failed: function unnest(unknown) is not unique` |
| **betroffene Tests** | `test_save_chunks_and_find_in_order`, `test_save_chunks_replaces_old_chunks`, `test_save_chunks_empty_text_fails`, `test_embeddings_round_trip_and_duplicate_ignored`, `test_find_embeddings_other_model_empty` |
| **Ursache** | psycopg schickt eine Liste von Strings ohne Datentyp; Postgres kennt mehrere `unnest`-Varianten und kann nicht wählen. In DataGrip fiel es nicht auf, weil dort ein typisiertes Array-Literal steht. |
| **Gefunden** | Rauchtest aller SQL-Dateien über Python am 14.11.2026 |
| **Behebung** | `unnest(%(texts)s::text[])` in `insert_chunks.sql` (15.11.2026); danach alle Storage-Tests grün |
| **Lehre** | SQL-Dateien nicht nur in der IDE testen, sondern auch über den Weg, den das Programm nimmt. |

### 6.2 Behoben: Division durch null in BM25 bei `k1 = 0`

| | |
|---|---|
| **Input** | `top_m` mit `k1 = 0` und einem Anfragewort, das in einem Dokument fehlt |
| **erwartet** | Score-Beitrag 0 für das fehlende Wort |
| **tatsächlich (vorher)** | `ZeroDivisionError`, weil `f + K` mit `f = 0` und `K = 0` null wird |
| **Behebung** | `compute_term_score` gibt bei `f = 0` sofort 0 zurück (Commit `bbe1a3f`, 15.10.2026); Regressionstests `test_term_score_k1_zero_missing_term`, `test_top_m_k1_zero_does_not_crash` |

### 6.3 Behoben: Tokenizer klebte Wörter zusammen

| | |
|---|---|
| **Input** | `"and/or"` (Beispiel aus der Commit-Nachricht) |
| **erwartet** | `["and", "or"]` |
| **tatsächlich (vorher)** | `["andor"]`: Satzzeichen wurden entfernt statt durch Leerzeichen ersetzt |
| **Behebung** | Satzzeichen werden zu Leerzeichen, Bindestriche im Wort verbinden, `casefold()` statt `lower()` (Commit `b861216`, 13.10.2026); Tests für Halbgeviertstrich, Geviertstrich (`"kam—und"` → `["kam", "und"]`), Bindestrich, Apostroph und „ß“ |

### 6.4 Behoben: Schema-Regeln durch einen Merge verloren

| | |
|---|---|
| **Input** | `schema.sql` nach Commit `0003932` |
| **erwartet** | alle entworfenen Regeln, z. B. `chunks_invalid_text` (E30), `searched_at DEFAULT now()` (E19) |
| **tatsächlich (vorher)** | eine ältere lokale Fassung überschrieb die Datei: Regel E30 fehlte, `searches.categories` erlaubte `NULL`, ein fehlendes Komma brach die Datei |
| **Behebung** | Commit `ca958c1` (09.11.2026), danach zweimal hintereinander fehlerfrei ausgeführt und alle Übungsdateien in `sql/uebungen/` erneut geprüft |
| **Lehre** | Nach jedem Merge `schema.sql` zweimal komplett ausführen; der Rauchtest vom 14.11. tut das jetzt auf beiden lokalen Datenbanken. |

### 6.5 Abweichung vom Entwurf: BM25 filtert auf Abstracts kaum vor

Kein Programmierfehler, aber eine Abweichung zwischen erwartetem und tatsächlichem Verhalten, gefunden mit 8 echten arXiv-Anfragen (`messungen/2026-10-19_review-pr24/`).

| | |
|---|---|
| **erwartet** (Pseudocode, Flowchart) | BM25 wählt aus allen Chunks die besten m = 50 aus, der Rest geht nicht an Voyage |
| **tatsächlich** | 20 Abstracts ergeben nur 22 bis 29 Chunks; aussortiert werden ≈ 10 %, nur Chunks ganz ohne Schlagwort |
| **Bewertung** | als Einschränkung dokumentiert (ADR 0004, Limitation L1 in `Phase5/Reflexion.md`); mit Volltext sortiert die Vorauswahl 90–96 % aus |

### 6.6 Lücken der Tests

- **`bm25` hat keinen Fehlerfall.** Das ist so entworfen: BM25 wirft nie, sondern liefert bei leerem Index, leerer Anfrage oder `m = 0` eine leere Liste (38 Randfälle). Nicht getestet ist ein negatives `m`.
- **Echte Netzwerkaufrufe** (`http_get`, `http_post_json`) und der Serverstart sind nicht durch Unittests abgedeckt (Abschnitt 4).
- **Die Qualität des Rankings** prüfen die Unittests nur an kleinen, ausgedachten Beispielen. Ob das Tool bei echten Fragen die richtige Quelle findet, beantworten erst die Messläufe (Karte #6).
- **Die Kategorien** ordnet ein Skript nach Testnamen zu; vier Fälle sind von Hand korrigiert. Einzelne Grenzfälle können anders gesehen werden.

## 7. Optional: Laufzeit und Vergleich mit Alternativen

**Laufzeit**
- Die gesamte Testsuite (325 Tests) läuft in etwa 1,2 s.
- Ein Tool-Aufruf mit Titel und Abstract dauert eine arXiv-Anfrage plus zwei Voyage-Aufrufe; die Rechenschritte selbst fallen daneben nicht ins Gewicht. Mit Volltext und ohne Cache wären es etwa 3,5 Minuten pro Aufruf (ADR 0004).

**Vergleich mit Alternativen**

| Vergleich | Ergebnis | Quelle |
|---|---|---|
| nur BM25 gegen hybrid (BM25 + Vektor + RRF + MMR) | im Prototyp nebeneinander ausgegeben; die echte Trefferquote folgt mit den Messläufen | `Phase3/Prototyp.ipynb`, Abschnitt 2.3 |
| Titel und Abstract gegen Volltext | Volltext: Vorauswahl sortiert 90–96 % statt 10 % aus, IDF des Hauptbegriffs steigt von 0,10 auf 0,62 | ADR 0004 |
| PDF-Extraktoren gegen die LaTeX-Quelle | `pypdf` gleich gut wie `pymupdf4llm`, siebenmal schneller, BSD-Lizenz | ADR 0004, `messungen/2026-10-19_review-pr24/` |
| Overlap 0 bis 100 Wörter | 40 liegt am Knick: 95,4 % der relevanten Sätze ganz in einem Chunk bei 6,7 % doppelten Wörtern | `docs/chunking/chunking-pseudocode.md` |
| klassische IDF gegen IDF mit +1 | klassische Variante wird bei df > N/2 negativ, +1-Variante bleibt positiv | ADR 0003 |
