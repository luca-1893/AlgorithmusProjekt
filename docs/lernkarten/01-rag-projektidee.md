# 01 RAG und Projektidee

**In einem Satz:** Ein regelbasierter Algorithmus sucht auf arXiv, sortiert die Treffer vor und gibt dem Sprachmodell nur die besten Textabschnitte mit Quelle zurück, als MCP-Tool `research_papers`.

## Kernidee

- **Problem:** Bei der Recherche mit KI kommt es zu Halluzinationen, und jede Recherche kostet Tokens und Zeit, weil das Sprachmodell selbst sucht und liest (README).
- **RAG (Retrieval Augmented Generation):** Erst passende Textstellen holen (Retrieval), dann antwortet das Modell auf Basis dieser Stellen (Generation).
- **Ziele:** weniger Halluzinationen (Antwort auf belegten Quellen), weniger Tokens und kürzere Laufzeit (Vorauswahl passiert algorithmisch, nicht im Modell).
- **Bausteine:** Chunking, BM25 über invertierten Index, Vektorsuche (Cosinus, Top-k per Heap), Rangfusion (RRF), Duplikat-Filter (MMR), MCP-Wrapper, Evaluation.
- **Selbst gebaut:** Die Algorithmus-Module nutzen nur die Standardbibliothek; Bibliotheken nur an den Rändern (FastMCP, psycopg, anthropic).
- **Kein Token-Budget:** Die Antwortgröße begrenzen `k` und die Chunk-Größe.

## Ablauf

```
Nutzerfrage → Sprachmodell erzeugt englische Schlagwörter
→ research_papers(keywords, k, question, ...)
→ arXiv (oder Cache) → Chunks → BM25 → Vektorsuche → RRF → MMR
→ k Abschnitte mit Titel, Autoren, Datum, Link als JSON → Modell antwortet mit Quelle
```

## Mini-Beispiel

Testfrage F21 (`docs/mcp_server/einrichtung.md`): „A method copies the terms that a cross-encoder treats as decisive … into the BM25 query. How much does it raise Recall@100 on Natural Questions?“ Erwartet: Claude ruft `research_papers` auf und zitiert arXiv **2608.00452**, Antwort „von 0,32 auf 0,47“.

## Im Projekt

- Einstieg: `src/pipeline/pipeline.py` → `research()`, Tool: `src/mcp_server/mcp_server.py`.
- Stack: Python 3.15, FastMCP, PostgreSQL 18, Voyage-Embeddings (ADR 0001, 0002).
- **Warum MCP-Tool:** Jeder MCP-Client (Claude Desktop, Claude Code) kann es ohne eigene Oberfläche aufrufen; das Modell entscheidet selbst, wann es recherchiert, und liefert die Schlagwörter. Eigene Logik bleibt in einem Server, der lokal (stdio) oder als Webdienst (HTTP) läuft.
- Token-Ersparnis bisher nur **geschätzt** (Prototyp, 4 Zeichen pro Token): alle 20 Abstracts ≈ 5.660 Tokens, Auswahl von 5 Chunks ≈ 1.951 Tokens, rund 66 % weniger (Reflexion L5). Die Messläufe laufen noch.

## Typische Prüferfragen

- **Was ist RAG?** Abrufen relevanter Textstellen aus einer Wissensbasis und Übergabe an das Sprachmodell, damit es auf belegten Quellen antwortet.
- **Warum nicht einfach die Websuche des Modells?** Das Modell liest dann ganze Seiten selbst (Tokens, Zeit). Genau das vergleichen die Messläufe: `agent_websearch` gegen `bm25` und `hybrid`.
- **Was ist „regelbasiert“ daran?** Der Ablauf ist durch Entscheidungsregeln R1–R16 festgelegt und deterministisch (Gleichstand: kleinere Position/ID zuerst, R12).
- **Weisen Sie weniger Halluzinationen nach?** Nein, nur indirekt über `found_source` (erwartete arXiv-ID steht in der Antwort). Richtig formuliert: „öfter die richtige Quelle gefunden“ (L6).

## Stolperfallen

- Die 66 % sind eine Schätzung gegen „alle Abstracts lesen“, kein Messergebnis.
- Das Tool sieht nur Titel und Abstract, keinen Volltext (ADR 0004, L3).
