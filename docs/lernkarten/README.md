# Lernkarten zum Pitch

Lernkarten für den Pitch am 30.11.2026 und die Rückfragen der Prüfer. Jede Karte behandelt ein Thema auf höchstens etwa einer DIN-A4-Seite: Kernidee, Formel oder Ablauf, ein kleines Beispiel mit Zahlen aus dem Projekt, Komplexität, wo es im Code steht, typische Prüferfragen mit Antwort und Stolperfallen.

Alle Zahlen stammen aus dem Repository (Pseudocode, Formelsammlungen, ADRs, Testdokumentation, Reflexion, Journal). Ergebnisse der Messläufe gibt es noch nicht; die Karten nennen deshalb keine gemessene Token-Ersparnis oder Trefferquote. Wo eine Zahl nur geschätzt ist, steht das dabei.

Formeln sind in einfacher Schreibweise ohne LaTeX gesetzt. Alle Karten zusammen: [Lernkarten.pdf](Lernkarten.pdf) (erzeugt mit pandoc nach HTML und Chromium-Druck, Stand 28.11.2026).

## Inhalt

| Nr. | Karte | Thema |
|---|---|---|
| 01 | [RAG und Projektidee](01-rag-projektidee.md) | Problem, Ziel, warum MCP-Tool |
| 02 | [Tokenizer und Chunking](02-tokenizer-chunking.md) | Normalisierung, Chunks mit Überlappung |
| 03 | [Invertierter Index](03-invertierter-index.md) | Wort → Dokumente, N, avgdl |
| 04 | [BM25](04-bm25.md) | TF, IDF (ADR 0003), k1/b, top_m, Handrechnung |
| 05 | [Embeddings und Cosinus](05-embeddings-cosinus.md) | Voyage, ADR 0001, Cosinus-Ähnlichkeit |
| 06 | [Top-k mit Heap](06-top-k-heap.md) | begrenzter Min-Heap, Gleichstand |
| 07 | [Reciprocal Rank Fusion](07-reciprocal-rank-fusion.md) | Ränge statt Rohwerte, k_rrf |
| 08 | [Score-Normalisierung](08-score-normalisierung.md) | Min-Max für MMR |
| 09 | [Maximal Marginal Relevance](09-maximal-marginal-relevance.md) | Relevanz gegen Vielfalt, λ |
| 10 | [Gesamtpipeline und Regeln](10-pipeline-regeln.md) | Ablauf, R1–R16 |
| 11 | [MCP und FastMCP](11-mcp-fastmcp.md) | Tool research_papers, stdio vs. HTTP |
| 12 | [arXiv und Suchfilter](12-arxiv-suchfilter.md) | Abfrage, Filter, R3 |
| 13 | [Relationales Schema](13-relationales-schema.md) | Schlüssel, CASCADE, CHECK, NULL |
| 14 | [SQL aus Python](14-sql-aus-python.md) | psycopg, Parameter, Transaktionen, Casts |
| 15 | [Index und EXPLAIN ANALYZE](15-index-explain.md) | ADR 0005 |
| 16 | [Cache-Strategie](16-cache-strategie.md) | R13–R16, 7 Tage, C1–C13 |
| 17 | [Evaluation und KPIs](17-evaluation-kpis.md) | Varianten, found_source, Leitfragen |
| 18 | [Teststrategie](18-teststrategie.md) | Kategorien, Coverage, Abweichungen |
| 19 | [Komplexität](19-komplexitaet.md) | alle Schritte im Überblick |
| 20 | [Limitationen](20-limitationen.md) | L1–L10 kurz |

## Quellen

`Phase2/Pseudocode.md`, `docs/<modul>/*-pseudocode.md` und `*-formelsammlung.md`, `docs/adr/`, `docs/storage/schema-entwurf.md`, `docs/storage/sql-cheatsheet.md`, `docs/cache/cache-pseudocode.md`, `docs/evaluation/`, `Phase4/Testdokumentation.md`, `Phase5/Reflexion.md`, `docs/journal.md`, Code in `src/` und `sql/`. Stand der Zahlen: 15.11.2026.
