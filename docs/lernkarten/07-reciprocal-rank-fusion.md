# 07 Reciprocal Rank Fusion (RRF)

**In einem Satz:** RRF verschmilzt die BM25-Rangliste und die Vektor-Rangliste zu einer, indem jeder Kandidat pro Liste 1 / (k_rrf + Rang) Punkte bekommt.

## Kernidee

- Es zählen nur **Ränge**, nicht die Rohwerte: BM25 ist nach oben offen, Cosinus liegt zwischen −1 und 1. Rohwerte zu addieren hieße, die Skala entscheidet.
- Wer in beiden Listen weit oben steht, gewinnt.
- Kommt ein Kandidat in einer Liste nicht vor, trägt diese Liste nichts bei.
- **k_rrf** glättet: 0 → Platz 1 zählt doppelt so viel wie Platz 2; 60 (Literatur-Standard) → Abstände oben schrumpfen; groß → es zählt vor allem, in wie vielen Listen ein Kandidat steht.
- Gleichstand: kleinere ID zuerst (R12).

## Formel

```
RRF(d) = Summe über alle Ranglisten r von 1 / (k_rrf + rang_r(d))      (Rang ab 1)
```

## Mini-Beispiel

Test `test_rrf_hand_calculated`: Listen `[1, 2]` und `[2, 3]`, k_rrf = 0

| Kandidat | Liste 1 | Liste 2 | RRF |
|---|---|---|---|
| 1 | 1/1 | – | 1,0 |
| 2 | 1/2 | 1/1 | **1,5** |
| 3 | – | 1/2 | 0,5 |

Ergebnis 2 > 1 > 3. Mit k_rrf = 60: 2 → 1/62 + 1/61 ≈ 0,0325; 1 → 1/61 ≈ 0,0164; 3 → 1/62 ≈ 0,0161.

## Komplexität

O(S + U · log U), S = Summe der Listenlängen, U = verschiedene Kandidaten. Im Projekt O(m · log m).

## Im Projekt

- `src/ranking/ranking.py` → `reciprocal_rank_fusion(rankings, k_rrf=60)`, gibt `(id, score)` absteigend zurück.
- Aufruf in `pipeline._hybrid`: `[bm25_ranking, vector_ranking]` über die Kandidaten aus der BM25-Vorauswahl (R8). Findet BM25 nichts, sind alle Chunks Kandidaten und die BM25-Liste ist leer, dann entscheidet nur die Vektorsuche.
- Der RRF-Score ist der `score` im JSON des hybriden Pfads; danach Normalisierung (Karte 08) und MMR (Karte 09).
- `k_rrf = 60` ist der Literaturwert, nicht selbst kalibriert (A11, L9).

## Typische Prüferfragen

- **Warum nicht die Scores addieren?** Verschiedene Skalen; BM25-Werte hängen von Korpus und Anfrage ab.
- **Was ist der höchstmögliche RRF-Score?** Anzahl Listen / (k_rrf + 1), also 2/61 bei zwei Listen.
- **Warum k_rrf = 60?** Standardwert aus der Literatur; er verhindert, dass Platz 1 einer einzigen Liste alles dominiert.
- **Was passiert mit einem Kandidaten, der nur in einer Liste steht?** Er bekommt nur dort Punkte und landet meist hinter Kandidaten aus beiden Listen.

## Stolperfallen

- Mit k_rrf = 60 liegen die Scores eng beieinander (≈ 0,016 bis 0,033); für MMR müssen sie deshalb auf 0 bis 1 normiert werden.
- `k_rrf < 0` ist ein Fehler (`ValueError`).
