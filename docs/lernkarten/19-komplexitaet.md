# 19 Komplexität im Überblick

**In einem Satz:** Alle lokalen Rechenschritte sind linear oder fast linear in der Datenmenge; die Laufzeit eines Tool-Aufrufs bestimmen das Netzwerk (arXiv, Voyage) und nicht die Algorithmen.

## Kernidee

- **Symbole:** T = Wörter aller Dokumente, C = BM25-Kandidaten, P = Postings der Anfragewörter, \|q\| = Anfragewörter, m = 50 Kandidaten, k = Treffer (Standard 5), d = Vektorlänge (1024), n = Listenlänge.
- **Heap statt Sortieren:** Top-k/Top-m in O(n · log k) statt O(n · log n).
- **Invertierter Index:** nur Postings der Anfragewörter lesen, nicht alle Dokumente.
- **BM25 als Vorauswahl:** begrenzt die teuren Schritte (Einbetten, Cosinus, MMR) auf m Kandidaten; auf Abstracts greift das kaum (L1).
- **Netzwerk dominiert:** ein arXiv-Aufruf und zwei Voyage-Aufrufe kosten mehr als alle Rechenschritte zusammen.

## Tabelle

| Schritt / Funktion | Laufzeit |
|---|---|
| `normalize_keywords` | O(L), L = Länge aller Schlagwörter |
| `build_arxiv_url` / `parse_arxiv_feed` | O(L + K) / O(X), X = Länge der Antwort |
| Cache abfragen | eine Datenbankabfrage; mit Index O(log n) statt Seq Scan O(n) |
| `tokenize` | O(C), C = Zeichen |
| `split_into_chunks` | O(n), n = Wörter |
| `build_index` | O(T) |
| `compute_idf`, `compute_term_score` | O(1) |
| `compute_score` | O(\|q\|) je Dokument |
| `top_m` | O(P + C · \|q\| + C · log m) |
| `cosine_similarity` | O(d) |
| `top_k` | O(n · log k), Speicher O(k) |
| `most_similar` (Vektorsuche) | O(n · d + n · log k); im Projekt O(m · d) |
| Einbetten | zwei API-Aufrufe; mit R16 nur für neue Chunks |
| `reciprocal_rank_fusion` | O(S + U · log U); im Projekt O(m · log m) |
| `normalize_scores` | O(n) |
| `mmr_select` | O(k · m · d) |

## Mini-Beispiel

MMR bei m = 50, k = 5, d = 1024: höchstens 5 · 50 · 1.024 ≈ 256.000 Multiplikationen, für einen Rechner vernachlässigbar. Mit Volltext wächst T um etwa das 20- bis 40-Fache (22–29 → 515–1.167 Chunks pro Anfrage); dann filtert die Vorauswahl 90–96 % aus und hält das Einbetten bei m Chunks (Reflexion).

## Im Projekt

- Quellen: `Phase2/Pseudocode.md` (Abschnitt Komplexität), Modul-Pseudocode `docs/<modul>/*-pseudocode.md`, `Phase5/Reflexion.md` (Wie skaliert die Lösung?).
- MMR effizient, weil die höchste Ähnlichkeit je Kandidat nach jeder Wahl nur mit dem neuen Vektor aktualisiert wird (sonst O(k² · m · d)).

## Typische Prüferfragen

- **Wo ist der Algorithmus ineffizient?** Netzwerk, Index pro Aufruf neu (O(T)), Einbetten fast aller Chunks auf Abstracts (L1).
- **Warum O(C · log m) und nicht O(C · log C) in top_m?** `heapq.nsmallest(m, …)` hält nur m Elemente.
- **Was skaliert schlecht?** Rechnerisch nichts; mehr Dokumente verschlechtern aber die IDF (L2), und arXiv drosselt die Anfragen.
- **Warum sind IDF-Berechnungen nicht pro Dokument?** Die IDF hängt nur vom Wort ab; sie wird einmal pro Anfragewort in `top_m` berechnet.

## Stolperfallen

- O-Notation ignoriert Konstanten: ein einziger HTTP-Aufruf ist teurer als alles Lokale.
- C (Kandidaten in BM25) nicht mit C (Zeichen im Tokenizer) verwechseln; im Gespräch die Bedeutung nennen.
