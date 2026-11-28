# Reflexion: Annahmen und Limitationen

Phase 5 des Hackathons (Karte #16). Stand: 15.11.2026, Prototyp auf `luca-dev`; L1–L3 und L7 nachgetragen am 28.11.2026 (Volltext, Branch `volltext`). Tests und Coverage: `Phase4/Testdokumentation.md`.

Grundlage sind die Messungen aus `messungen/2026-10-19_review-pr24/` (8 echte arXiv-Anfragen aus verschiedenen Fachgebieten, je 20 Dokumente), die ADRs unter `docs/adr/` und der Prototyp `Phase3/Prototyp.ipynb`. Die KPI-Messläufe (Karte #6) stehen noch aus; wo Ergebnisse daraus fehlen, ist das markiert.

## 1. Annahmen und Vereinfachungen

| Nr. | Annahme oder Vereinfachung | Warum | Wo beschlossen |
|---|---|---|---|
| A1 | Bis 28.11.2026 nur Titel und Abstract; seitdem Volltext per Schalter (MCP-Server an, Messlauf nur mit `--volltext`) | Volltext kostet ohne Cache etwa 3,5 Minuten pro Tool-Aufruf; mit Cache nur beim ersten Abruf | ADR 0004, ADR 0006 |
| A2 | arXiv ist die einzige Quelle | Offene API, keine Anmeldung; Google Scholar hat keine offizielle API | Karte #21 |
| A3 | Chunks werden in Wörtern gemessen, nicht in LLM-Tokens | Kein Tokenizer des Sprachmodells nötig, unabhängig vom Modell | `docs/chunking/chunking-pseudocode.md` |
| A4 | Kein Token-Budget; die Antwortgröße begrenzen `k` und die Chunk-Größe | Einfacher und erklärbarer als eine Knapsack-Auswahl | Entscheidung vom 10.10., Knapsack als Übung (#10) |
| A5 | Ein BM25-„Dokument“ ist ein Chunk, die IDF wird über die Chunks des Treffersatzes berechnet | Es gibt keinen festen Korpus, nur das, was arXiv gerade liefert | `Phase2/Pseudocode.md` |
| A6 | IDF mit +1 (Lucene-Variante) | Bleibt auch bei kleinen Korpora positiv | ADR 0003 |
| A7 | Embeddings kommen über eine API (Voyage AI, `voyage-4`, 1024 Dimensionen) | Keine Rechenlast und kein Modell auf dem Server | ADR 0001 |
| A8 | Dokumente und Vektoren veralten nicht, nur Suchergebnisse (7 Tage) | Gleicher Text und gleiches Modell ergeben denselben Vektor; neue Paper erscheinen täglich | `Phase2/Pseudocode.md`, R13–R16 |
| A9 | Relevanz (BM25-Score, Cosinus) wird nie gespeichert | Sie hängt von der Anfrage ab | `Phase2/Pseudocode.md` |
| A10 | Halluzinationen werden über `found_source` angenähert: Steht die erwartete arXiv-ID unter den Belegen, gilt die Antwort als belegt | Halluzinationen direkt zu bewerten ist kaum zuverlässig möglich | `docs/evaluation/leitfragen.md`, E33 |
| A11 | Parameter: `chunk_size` 200, `overlap` 40, `candidates_m` 50, `k_rrf` 60, `λ` 0,7, `max_documents` 20 | Nur `overlap` ist gemessen; `k_rrf` ist der Standardwert aus der Literatur, die übrigen sind gesetzt | `PipelineConfig` in `src/pipeline/pipeline.py` |

## 2. Limitationen

Jede Limitation folgt demselben Aufbau: **Was** ist eingeschränkt, **woher** wissen wir es (Messung oder Quelle), **warum** passiert es, **was bedeutet** es für den Nutzer, **wie geht der Prototyp** heute damit um, und **was würde es lösen**.

### Überblick

| Nr. | Limitation | Schwere | Status |
|---|---|---|---|
| L1 | BM25-Vorauswahl greift auf Abstracts kaum | hoch | Volltext + Cache umgesetzt (ADR 0006), im Messlauf noch nicht gemessen |
| L2 | IDF hängt am Treffersatz, das Hauptschlagwort zählt kaum | hoch | durch Volltext entschärft (umgesetzt), Lösung geplant (IDF über die Datenbank) |
| L3 | Antworten nur im Volltext werden nicht gefunden | hoch | Volltext umgesetzt (ADR 0006), im Messlauf noch nicht gemessen (L6) |
| L4 | Deutsche Schlagwörter finden kaum etwas | mittel | offen |
| L5 | Token-Ersparnis bisher nur geschätzt | hoch für den Pitch | Messung offen (Karte #6) |
| L6 | Halluzinationen nur indirekt gemessen | mittel | bewusste Entscheidung (E33) |
| L7 | Abhängigkeit von arXiv und Voyage, stiller Rückfall auf BM25 | mittel | Fehlerpfade getestet; Wiederholen bei 429 für Volltext-Downloads umgesetzt, für Suche und Voyage offen |
| L8 | Wörter statt Tokens, zerrissene Sätze, Redundanz | niedrig | gemessen, `overlap = 40` begründet |
| L9 | Parameter nicht für arXiv kalibriert | mittel | offen |
| L10 | Kleinere Grenzen (Seitenzahl, Anmeldung, Index pro Aufruf, Testabdeckung) | niedrig | dokumentiert |

Vorschlag für den Pitch (fünf Folien-Punkte): L2, L1, L3, L6, L7.

### L1: Die BM25-Vorauswahl greift auf Abstracts kaum

**Was:** Laut Entwurf (Pseudocode, Flowchart) ist BM25 ein Filter: Aus allen Chunks kommen nur die besten m = 50 weiter, nur diese werden eingebettet. Auf Titel und Abstract filtert BM25 aber fast nichts.

**Beleg:** 8 echte arXiv-Anfragen mit je 20 Dokumenten. 20 Abstracts ergeben nur 22 bis 29 Chunks, also weniger als m. `top_m` gibt dann jeden Chunk zurück, der überhaupt ein Schlagwort enthält. Von 207 Chunks über alle Anfragen sortiert die Vorauswahl nur 21 aus (≈ 10 %), und zwar ausschließlich Chunks ganz ohne Schlagwort. Bei 50 Dokumenten schneidet m erst 5–12 Chunks ab, bei 100 Dokumenten 59–69.

**Warum:** Die meisten Abstracts passen bei `chunk_size = 200` in einen einzigen Chunk (20 Abstracts ergeben 22–29 Chunks). Die Zahl der Chunks ist damit ungefähr die Zahl der Dokumente, und die liegt mit `max_documents = 20` unter m.

**Bedeutung:** Im hybriden Weg gehen fast alle Chunks an Voyage. Die Annahme aus ADR 0001, dass BM25 die Embedding-Kosten klein hält, gilt auf Abstracts nicht. BM25 wirkt hier vor allem als zweites Ranking-Signal in der Rangfusion, nicht als Filter.

**Heute:** In der Abstract-Variante (Messlauf ohne `--volltext`) gilt die Einschränkung weiter (ADR 0004). Seit dem 28.11.2026 lädt das Tool den Volltext (ADR 0006, R17), im MCP-Server standardmäßig. Im Rauchtest (`["BM25", "information retrieval"]`, 5 Dokumente) entstanden daraus 278 Chunks; wie viel die Vorauswahl im Messlauf aussortiert und ob die Antworten besser werden, ist **noch nicht gemessen**.

**Lösung:** Volltext statt Abstract (umgesetzt). Mit Volltext entstehen 515–1.167 Chunks pro Anfrage, und die Vorauswahl sortiert 90–96 % aus. Das kostet ohne Cache etwa 3,5 Minuten pro Aufruf und ist deshalb erst mit dem Datenbank-Cache sinnvoll. Die Alternative, `max_documents` auf 50–100 zu erhöhen, wurde verworfen, weil sie L2 verschärft.

### L2: Die IDF hängt am Treffersatz

**Was:** BM25 gewichtet jedes Anfragewort mit seiner IDF: Seltene Wörter zählen mehr. Im Tool zählt ausgerechnet das wichtigste Schlagwort am wenigsten.

**Beleg:**

| Term | IDF bei 20 Abstracts | bei Volltext |
|---|---|---|
| `uml` | 0,10 | 0,62 |
| `retrieval` | 0,10 | 0,62 |
| `transformer` | 0,22 | 0,81 |
| `bm25` | 2,01 | – |

Bei „quantum error correction“ liegen alle drei Terme zwischen 0,10 und 0,14, bei 100 Dokumenten nur noch bei 0,04 bis 0,06.

**Warum:** Es gibt keinen festen Korpus. Die IDF wird über die Chunks berechnet, die arXiv gerade für diese Schlagwörter geliefert hat (A5). arXiv liefert die Dokumente aber genau deshalb, weil sie die Schlagwörter enthalten. Das Hauptschlagwort steht so in 81–92 % aller Chunks, seine IDF geht gegen null. Das ist kein Rechenfehler, sondern die richtige Formel auf dem falschen Korpus.

**Bedeutung:** BM25 rankt praktisch nach Nebenbegriffen und nach der Textlänge. Ein Chunk, der das Hauptthema ausführlich behandelt, kann hinter einem Chunk landen, der zufällig einen seltenen Nebenbegriff enthält. Mehr Dokumente machen es schlimmer, nicht besser. Lucas ursprüngliche Idee, ein seltenes Schlagwort solle mehr zählen als die bloße Wiederholung des Suchworts, leistet BM25 zwar über IDF und Sättigung, aber nur auf einem passenden Korpus.

**Heute:** dokumentiert (ADR 0004). Volltext entschärft das Problem (`uml` 0,10 → 0,62 in der Messung vom 19.10.), löst es aber nicht: Das Hauptschlagwort bleibt meist der schwächste Term. Der Volltext ist seit dem 28.11.2026 umgesetzt (ADR 0006), die IDF über die Datenbank noch nicht.

**Lösung:** Die IDF über alle gespeicherten Chunks in der Datenbank berechnen, also über einen Korpus, der mit jeder Recherche wächst und nicht nur aus Treffern besteht. Voraussetzung sind Cache und eine `top_m`-Variante, die eine fertige IDF-Tabelle annimmt.

### L3: Antworten, die nur im Volltext stehen, findet das Tool nicht

**Was:** Der Prototyp sieht nur Titel und Abstract (A1).

**Beleg:** Folgt aus dem Aufbau; die Messfragen sollen dazu etwa zur Hälfte Fragen enthalten, deren Antwort nur im Volltext steht (`docs/evaluation/testfragen.md`, Leitfrage L6).

**Warum:** Volltext braucht pro Paper bis zu zwei Downloads (HTML, sonst PDF) mit Pause dazwischen, weil arXiv auch bei 3,1 s Abstand mit HTTP 429 drosselt. Ohne Cache sind das etwa 3,5 Minuten pro Tool-Aufruf; für ein Werkzeug, das ein Sprachmodell während einer Antwort aufruft, ist das zu langsam.

**Bedeutung:** Für Detailfragen (eine Zahl aus einer Tabelle, ein Verfahren aus dem Methodenteil, eine Einschränkung aus der Diskussion) liefert das Tool bestenfalls das richtige Paper, aber nie die richtige Stelle. Das Sprachmodell müsste dann selbst nachlesen, und die Token-Ersparnis (L5) wäre dahin.

**Heute:** umgesetzt am 28.11.2026, aber **noch nicht im Messlauf gemessen**. Das Tool lädt pro Paper die HTML-Fassung, sonst das PDF mit `pypdf`, sonst bleibt das Abstract mit Hinweis in `warnings` (R17, ADR 0006). Der Cache speichert `origin` und `full_text`; eine wiederholte Suche kommt ohne Download aus (Rauchtest: erster Abruf 15,9 s bei 5 Dokumenten, aus dem Cache 0,1 s). Wiederverwendet wird ein Volltext bisher nur über die gleiche Suche, nicht über die arXiv-ID. Die Abstract-Variante bleibt für den Vergleich in Leitfrage L6 erhalten (`messlauf` ohne `--volltext`).

**Lösung:** Volltext mit `pypdf` (gleich gut wie `pymupdf4llm`, siebenmal schneller, BSD-Lizenz), Wiederholen mit wachsender Wartezeit bei 429, Cache in PostgreSQL (umgesetzt). Offen: Messlauf mit `--volltext` und Vergleich nach L6.

### L4: Deutsche Schlagwörter finden kaum etwas

**Was:** arXiv ist fast vollständig englischsprachig.

**Beleg:** im Prototyp als Grenze festgehalten (`Phase3/Prototyp.ipynb`, Abschnitt 5), noch nicht gemessen; das macht Leitfrage L5 (deutsche gegen englische Fragen).

**Warum:** Die arXiv-Suche und BM25 vergleichen Wörter. „Klassendiagramm“ trifft kein Paper, das „class diagram“ schreibt. Die Vektorsuche ist sprachübergreifend, wirkt aber erst nach der arXiv-Suche: Sie kann die Frage auf Deutsch verstehen, aber keine Dokumente finden, die arXiv gar nicht geliefert hat.

**Bedeutung:** Das Tool hängt davon ab, dass das Sprachmodell englische Fachbegriffe als Schlagwörter erzeugt. Garantiert ist das nicht.

**Heute:** Die Tool-Beschreibung im MCP-Server verlangt schon „2 to 8 English technical terms“. Ob sich das Sprachmodell daran hält, zeigt erst die Messung.

**Lösung:** Nicht-englische Schlagwörter im Tool erkennen und mit einem Hinweis zurückweisen, oder die Schlagwörter vor der Suche übersetzen (zusätzlicher Aufruf, zusätzliche Fehlerquelle).

### L5: Die Token-Ersparnis ist bisher nur geschätzt

**Was:** Das Projektziel „Token-Ersparnis“ ist noch nicht gemessen.

**Beleg:** Im Prototyp ergibt die Schätzung mit etwa 4 Zeichen pro Token: alle 20 Abstracts ≈ 5.660 Tokens, die Auswahl von 5 Chunks als JSON ≈ 1.951 Tokens, also rund 66 % Ersparnis.

**Warum nur geschätzt:** Die echte Messung braucht Messfragen mit bekannter Quelle und Läufe eines Agenten mit exakten Tokenzahlen aus der API. Beides ist vorbereitet (`runs`, `insert_run.sql`, `kpi_by_variant.sql`, `storage.save_run`), die Fragen sind aber noch nicht gesammelt.

**Bedeutung:** Die Schätzung hat drei Schwächen. Die Faustregel „4 Zeichen pro Token“ ist ungenau, besonders bei Fachbegriffen und Formeln. Sie vergleicht mit „alle Abstracts lesen“, nicht mit dem, was ein Agent ohne Tool wirklich tut (er sucht im Web, liest Seiten, folgt Links), die echte Ersparnis kann also deutlich größer oder kleiner sein. Und die Metadaten im JSON (Autoren, Link, Kategorien) kosten selbst Tokens.

**Heute:** als Schätzung gekennzeichnet; Leitfrage L1 legt das Erfolgskriterium vorher fest (Vorschlag: mindestens 50 % weniger Input-Tokens).

**Lösung:** Messläufe nach `docs/evaluation/testfragen.md` mit den Varianten `agent_websearch`, `bm25` und `hybrid`, gleiches Modell und gleicher System-Prompt. Die Zahl der Messfragen ist noch festzulegen; je weniger Fragen, desto grober die Trefferquote.

### L6: Halluzinationen werden nur indirekt gemessen

**Was:** Das zweite Projektziel „weniger Halluzinationen“ wird nicht direkt bewertet.

**Beleg:** Entscheidung E33 (`docs/evaluation/leitfragen.md`): Als Näherung gilt `found_source`, also ob die erwartete arXiv-ID unter den Belegen der Antwort steht.

**Warum:** Ob eine Antwort halluziniert, lässt sich nur durch Vergleich mit der Quelle Satz für Satz beurteilen. Das ist aufwendig und subjektiv, im Rahmen des Hackathons nicht zuverlässig machbar.

**Bedeutung:** Eine Antwort kann die richtige Quelle zitieren und trotzdem etwas Falsches behaupten, zum Beispiel eine Zahl verdrehen. `found_source` zeigt nur, dass die Antwort **belegbar** ist, nicht dass sie **richtig** ist. Im Pitch darf deshalb nicht „weniger Halluzinationen nachgewiesen“ stehen, sondern „öfter die richtige Quelle gefunden“.

**Heute:** bewusste Entscheidung, so in den Leitfragen festgehalten.

**Lösung:** Stichprobe von Hand bewerten (z. B. jede fünfte Antwort gegen die Referenzantwort aus `testfragen.md`) oder ein zweites Sprachmodell als Bewerter mit fester Bewertungsskala; beides mit eigener Unsicherheit.

### L7: Abhängigkeit von externen Diensten

**Was:** Das Tool braucht zwei fremde Dienste: arXiv für die Dokumente, Voyage AI für die Vektoren.

**Beleg:** Fehlerpfade sind getestet (Testdokumentation, F4–F6). Beobachtet: arXiv drosselt mit HTTP 429 auch bei 3,1 s Abstand (ADR 0004).

**Warum:** Das ist der Preis für zwei Entscheidungen. Live-Recherche statt festem Korpus (aktuelle Paper, kein eigenes Archiv) und Embeddings über eine API statt lokal (ADR 0001: kein Modell und keine Rechenlast auf dem Server).

**Bedeutung:**
- Fällt **arXiv** aus, liefert das Tool nichts, außer die Suche liegt schon im Cache (seit 15.11. umgesetzt, R13–R15).
- Fällt **Voyage** aus (Schlüssel ungültig, Limit, Netz), fällt die Pipeline still auf reines BM25 zurück (R10). Das ist gewollt, weil die Recherche nicht scheitern soll, aber der Hinweis „Vektorsuche nicht verfügbar, nur BM25“ im Ergebnis ist das einzige Signal. Liest das Sprachmodell ihn nicht, merkt der Nutzer nicht, dass er schlechtere Treffer bekommt.
- Bei HTTP 429 werden seit dem 28.11.2026 nur die Volltext-Downloads wiederholt (5, 10, 20 s Wartezeit, dann Abstract, R17). Die Suchanfrage an die arXiv-API und Voyage werden weiterhin nicht wiederholt.
- Jeder Aufruf verursacht Voyage-Kosten, und wegen L1 für fast alle Chunks.

**Heute:** Beide Ausfälle führen zu verständlichen Fehlern oder einem geregelten Ausweichweg, nicht zum Absturz.

**Lösung:** Der Cache (R13–R15, umgesetzt) spart die arXiv-Abfrage bei Wiederholungen innerhalb von 7 Tagen, gemessen 3,5 s → 1,7 s; R16 spart zusätzlich das Einbetten bekannter Chunks, gemessen 2,3 s → 0,3 s bei einer wiederholten Anfrage; Wiederholen mit wachsender Wartezeit bei 429; gespeicherte Vektoren werden nicht neu berechnet (R16).

### L8: Wörter statt Tokens, zerrissene Sätze und Redundanz

**Was:** Das Chunking ist bewusst einfach: feste Wortzahl mit Überlappung.

**Beleg:** Overlap-Messung auf 160 Volltexten (`docs/chunking/chunking-pseudocode.md`): Bei `overlap = 40` liegen 95,4 % der relevanten Sätze ganz in einem Chunk, 4,6 % sind zerrissen. Der Overlap kostet 6,7 % doppelte Wörter in der Vorauswahl; 55 % der Top-m-Chunks haben ihren Nachbarn ebenfalls in der Auswahl.

**Warum:** Wörter statt LLM-Tokens (A3), damit das Chunking ohne Tokenizer des Sprachmodells auskommt und für jedes Modell gleich ist. Absätze und Zeilenumbrüche gehen beim Zerlegen verloren; ein Chunk beginnt und endet, wo die Wortzahl erreicht ist, nicht am Satzende.

**Bedeutung:**
- Wie viele Tokens ein Chunk kostet, schwankt mit Sprache und Fachbegriffen; die Antwortgröße ist nur ungefähr planbar.
- Ein zerrissener Satz kann seine Aussage verlieren („… nicht“ steht im nächsten Chunk).
- Benachbarte Chunks im Ergebnis wiederholen sich teilweise und kosten Tokens doppelt.
- MMR mit λ = 0,7 lässt Fast-Duplikate durch, z. B. zwei Fassungen desselben Papers.

**Heute:** `overlap = 40` liegt am Knick der Messung und bleibt.

**Lösung:** Benachbarte Treffer zu einem Abschnitt zusammenfassen (vorgemerkt); Chunks an Satzgrenzen ausrichten; Duplikate über die DOI erkennen.

### L9: Die Parameter sind nicht für arXiv kalibriert

**Was:** Von sechs Parametern ist nur einer gemessen (A11).

**Beleg:** `overlap = 40` ist gemessen (L8). `k_rrf = 60` ist der Standardwert aus der Literatur. `λ = 0,7`, `chunk_size = 200`, `candidates_m = 50` und `max_documents = 20` sind gesetzt.

**Warum:** Kalibrieren braucht eine Bewertung, welches Ergebnis besser ist, also die Messfragen mit bekannter Quelle (Karte #6). Ohne sie würde man auf Bauchgefühl optimieren.

**Bedeutung:** L1 zeigt, dass zwei Parameter nicht zueinander passen: Mit `max_documents = 20` entstehen weniger Chunks, als `candidates_m = 50` abschneiden könnte. Ob ein anderes λ bessere Antworten liefert, ist unbekannt.

**Heute:** dokumentiert; Hackathon-Regel 2 („Funktionalität vor Effizienz“) rechtfertigt, erst nach den Tests zu kalibrieren.

**Lösung:** Mit den Messfragen ein kleines Raster ausprobieren (z. B. λ ∈ {0,5; 0,7; 0,9}, m an k koppeln) und die Trefferquote vergleichen.

### L10: Weitere Grenzen

- **Seitenzahl ist kein Filter**, obwohl Lucas ursprüngliche Tool-Idee sie vorsah. arXiv nennt sie nur unregelmäßig im Kommentarfeld.
- **Keine Anmeldung:** Der MCP-Server läuft über HTTP ohne Anmeldung und darf nur hinter einem abgesicherten Zugang betrieben werden (VPN oder Reverse-Proxy mit Token).
- **Index pro Aufruf:** Chunking und invertierter Index werden bei jedem Aufruf neu gebaut, weil es keinen festen Korpus gibt. Bei 20 Abstracts unkritisch, mit Volltext spürbar.
- **Testabdeckung:** 97 % insgesamt, die Algorithmus-Module 100 %. Nicht durch Unittests abgedeckt sind echte Netzwerkaufrufe und der Serverstart; die Qualität des Rankings prüfen die Unittests nur an kleinen, ausgedachten Beispielen (`Phase4/Testdokumentation.md`, Abschnitt 6.6).
- **Nur eine Quelle:** arXiv deckt vor allem Informatik, Physik und Mathematik ab; Verlagsartikel und andere Fächer fehlen.

## 3. Leitfragen

### Wo ist der Algorithmus ineffizient?

- **Netzwerk dominiert:** Ein arXiv-Request und zwei Voyage-Aufrufe kosten mehr als alle Rechenschritte zusammen. Der Cache spart bei einer wiederholten Suche den arXiv-Request (gemessen 3,5 s → 1,7 s); seit R16 entfällt bei bekannten Chunks auch das Einbetten, übrig bleibt ein Voyage-Aufruf für die Frage (gemessen 2,3 s → 0,3 s).
- **Index pro Aufruf:** Chunking und invertierter Index werden jedes Mal neu gebaut, O(T) über alle Wörter. Bei 20 Abstracts unkritisch, mit Volltext (25 → 997 Chunks bei der UML-Anfrage) deutlich spürbar.
- **Einbetten fast aller Chunks:** Weil die Vorauswahl auf Abstracts kaum filtert (L1), gehen fast alle Chunks an Voyage. Das widerspricht der Annahme aus ADR 0001, dass BM25 die Kosten klein hält.
- **MMR:** O(k · m · d) mit d = 1024; bei m = 50 und kleinem k unkritisch.

### Welche Annahmen sind problematisch?

- **A5 (IDF über den Treffersatz)** ist die problematischste: Sie führt direkt zu L2.
- **A1 (nur Abstracts)** führt zu L1 und L3.
- **A10 (`found_source` als Ersatz)** misst das Projektziel nur teilweise (L6).
- **A11:** Die Parameter sind gesetzt, nicht begründet gemessen (L9).

### Wie skaliert die Lösung?

| Schritt | Laufzeit |
|---|---|
| Quelle abfragen | ein HTTP-Aufruf, dominiert vom Netzwerk |
| Chunking und Indexaufbau | O(T), T = Wörter aller Dokumente |
| BM25-Vorauswahl | O(P + C · \|q\| + C · log m) |
| Einbetten | zwei API-Aufrufe; mit Cache nur für neue Chunks |
| Vektorsuche | O(m · d) |
| Rangfusion | O(m · log m) |
| MMR | O(k · m · d) |

Mehr Dokumente skalieren rechnerisch linear, verschlechtern aber die IDF (L2). Mit Volltext wächst T um etwa das 20- bis 40-fache (Chunks pro Anfrage 22–29 → 515–1.167); dann wird die Vorauswahl wirksam und hält die Embedding-Kosten bei m Chunks. Die eigentliche Grenze ist die Drosselung durch arXiv, nicht die Rechenzeit.

### Welche realen Einschränkungen gibt es?

- Nur arXiv, also nur Preprints aus Naturwissenschaft und Informatik; andere Fächer und Verlagsartikel fehlen.
- Volltexte nur bei Open Access; arXiv ist Open Access, andere Quellen wären es oft nicht.
- Laufende Kosten und Schlüssel für Voyage.
- arXiv-Nutzungsregeln (Abstand zwischen Requests) begrenzen den Durchsatz.

## 4. Offen bis zum Pitch

- [ ] Ergebnisse der Messläufe (Karte #6) bei L5 und L6 eintragen
- [ ] Prüfen, ob die Reihenfolge der Limitationen für den Pitch passt (die 5 wichtigsten nach vorn)
- [x] Nach Cache und Volltext: Status von L1 bis L3 aktualisieren (28.11.2026, umgesetzt, noch nicht gemessen)
- [ ] Messlauf mit `--volltext` und Vergleich mit der Abstract-Variante (Leitfrage L6), danach L1 und L3 mit Zahlen
