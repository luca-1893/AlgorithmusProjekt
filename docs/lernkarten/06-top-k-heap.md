# 06 Top-k mit Heap

**In einem Satz:** Ein Min-Heap mit höchstens k Einträgen findet die k besten Werte einer Liste in O(n · log k), ohne alles zu sortieren.

## Kernidee

- **Min-Heap:** Binärbaum, bei dem das kleinste Element oben liegt; Einfügen und Entfernen O(log Größe), oberstes Element lesen O(1).
- Der Heap hält immer die **k besten bisher gesehenen** Werte; oben liegt der schwächste davon.
- Neuer Wert verdrängt das oberste Element nur, wenn er besser ist.
- **Gleichstand (R12):** Eintrag `(score, −position)`; bei gleichem Score gilt die größere Position als schwächer und fliegt zuerst.
- Am Ende den Heap (k Elemente) absteigend sortieren: O(k · log k).

## Ablauf

```
heap = leerer Min-Heap
FÜR position, score IN scores:
    eintrag = (score, −position)
    WENN Größe(heap) < k:           heap.einfügen(eintrag)
    SONST WENN eintrag > heap.oben: heap.oben ersetzen durch eintrag
GIB heap absteigend sortiert als (position, score) ZURÜCK
```

## Mini-Beispiel

Test `test_top_k_example`: `top_k([0.2, 0.9, 0.5, 0.7], k = 2)`

| Schritt | Eintrag | Heap danach (oben zuerst) |
|---|---|---|
| Position 0 | (0,2, 0) | einfügen → [0,2] |
| Position 1 | (0,9, −1) | einfügen → [0,2; 0,9] |
| Position 2 | (0,5, −2) > 0,2 | ersetzen → [0,5; 0,9] |
| Position 3 | (0,7, −3) > 0,5 | ersetzen → [0,7; 0,9] |

Ergebnis: `[(1, 0.9), (3, 0.7)]`. Gleichstand: `top_k([0.5, 0.5, 0.5], 2)` → `[(0, 0.5), (1, 0.5)]`.

## Komplexität

| Variante | Laufzeit | Speicher |
|---|---|---|
| alles sortieren, erste k nehmen | O(n · log n) | O(n) |
| **Min-Heap mit höchstens k Einträgen** | O(n · log k) | O(k) |

## Im Projekt

- `src/vector_search/vector_search.py` → `top_k(scores, k)` von Hand mit `heapq.heappush`/`heapreplace`; `most_similar` nutzt es für die Vektor-Rangliste.
- `src/bm25/bm25.py` → `top_m` nutzt `heapq.nsmallest(m, ...)` auf `(−score, doc_id)`: das Minus macht den höchsten Score zum „kleinsten“, bei Gleichstand gewinnt die kleinere `doc_id`.
- Werte: `m = 50` in BM25; im hybriden Pfad wird `most_similar` mit k = Anzahl Kandidaten aufgerufen (volle Rangliste für RRF).

## Typische Prüferfragen

- **Warum Min-Heap und nicht Max-Heap für die besten k?** Man muss schnell den schwächsten der k Besten finden und ersetzen; der liegt im Min-Heap oben.
- **Wann lohnt sich der Heap?** Wenn k deutlich kleiner als n ist; bei k = n ist es wie Sortieren.
- **Wie wird der Gleichstand deterministisch?** Über die Position im Tupel, nicht über Zufall oder Dict-Reihenfolge (R12).
- **Was liefert top_k bei k > n?** Genau min(k, n) Einträge.

## Stolperfallen

- `k ≤ 0` ist ein Fehler (`ValueError`), `top_m` mit `m ≤ 0` liefert dagegen eine leere Liste.
- Ohne `−position` würde bei Gleichstand die größere Position bevorzugt.
