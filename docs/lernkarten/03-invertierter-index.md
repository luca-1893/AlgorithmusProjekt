# 03 Invertierter Index

**In einem Satz:** Der invertierte Index ordnet jedem Wort die Dokumente zu, in denen es vorkommt, samt Häufigkeit, sodass BM25 nur die Dokumente der Anfragewörter anfassen muss.

## Kernidee

- „Invertiert“: nicht Dokument → Wörter, sondern **Wort → (Dok-ID → Anzahl)**. Die Liste je Wort heißt Postingliste.
- Nebenbei entstehen die Werte, die BM25 braucht: Länge je Dokument (`laenge`), Anzahl nicht-leerer Dokumente `N`, Durchschnittslänge `avgdl`.
- Dokumenthäufigkeit eines Worts = Länge seiner Postingliste: `n(q) = len(index[q])`.
- Termhäufigkeit = Eintrag in der Postingliste: `f(q, D) = index[q][D]`.
- Leere Dokumente werden übersprungen; die IDs der anderen bleiben stabil (Dok-ID = Position in der Liste).
- `k1`, `b` gehören nicht in den Index, sondern zur Suche.

## Ablauf

```
FÜR i, dok IN korpus:
    tokens = tokenisiere(dok)
    WENN tokens leer: WEITER
    laenge[i] = Anzahl tokens
    FÜR wort IN tokens: index[wort][i] = index[wort][i] + 1
N = Anzahl Einträge in laenge
avgdl = Summe(laenge) / N   (0 bei leerem Korpus)
```

## Mini-Beispiel

Korpus aus dem Test (`src/bm25/test_bm25.py`): `["Apfel apfel Banane.", "Banane, Milch!", ".!?", "Apfel Brot Milch Käse Butter"]`

| Wort | Postingliste |
|---|---|
| apfel | {0: 2, 3: 1} |
| banane | {0: 1, 1: 1} |
| milch | {1: 1, 3: 1} |
| brot, käse, butter | je {3: 1} |

Dokument 2 besteht nur aus Satzzeichen und wird übersprungen: `laenge = {0: 3, 1: 2, 3: 5}`, `N = 3`, `avgdl = 10 / 3 ≈ 3,33`.

## Komplexität

Aufbau O(T), T = Tokens im Korpus (streng O(C) über die Zeichen). Nachschlagen eines Worts O(1) (Dict). Kandidaten sammeln O(P), P = Summe der Postinglängen der Anfragewörter, statt alle Dokumente zu prüfen.

## Im Projekt

- `src/bm25/bm25.py` → `build_index(corpus)` gibt `(index, doc_lengths, n_docs, avgdl)` zurück.
- Ein „Dokument“ für BM25 ist ein **Chunk** (A5); der Index wird bei jedem Tool-Aufruf über die Chunks des Treffersatzes neu gebaut (L10).
- R11: Ein Anfragewort, das in keinem Chunk vorkommt, trägt nichts bei; leere Dokumente werden beim Aufbau übersprungen.

## Typische Prüferfragen

- **Warum invertiert statt jedes Dokument durchsuchen?** Bei einer Anfrage werden nur die Postinglisten der wenigen Anfragewörter gelesen, nicht der ganze Korpus.
- **Warum Dict von Dict?** O(1) für „kommt Wort w in Dokument d vor, wie oft?“ und für die Dokumenthäufigkeit.
- **Was passiert mit leeren Dokumenten?** Sie zählen nicht zu `N` und `avgdl`, ihre Position wird aber nicht neu vergeben.
- **Warum wird der Index jedes Mal neu gebaut?** Es gibt keinen festen Korpus, nur das, was arXiv gerade liefert; bei 20 Abstracts unkritisch.

## Stolperfallen

- Kommt ein Dokument dazu, ändern sich `N` und `avgdl` und damit die IDF jedes Worts.
- Ohne denselben Tokenizer für Index und Anfrage findet `"APFEL, Milch!"` nichts; deshalb wird auch die Anfrage tokenisiert.
