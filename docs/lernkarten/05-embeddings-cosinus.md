# 05 Embeddings und Cosinus-Ähnlichkeit

**In einem Satz:** Ein Embedding-Modell macht aus Text einen Zahlenvektor, und die Cosinus-Ähnlichkeit misst, wie ähnlich zwei Texte inhaltlich sind, auch ohne gemeinsame Wörter.

## Kernidee

- **Embedding:** Vektor fester Länge d, ähnliche Bedeutung → ähnliche Richtung. Funktioniert sprachübergreifend (deutsche Frage, englischer Abstract).
- **Cosinus:** Winkel zwischen zwei Vektoren, unabhängig von ihrer Länge. 1 = gleiche Richtung, 0 = nichts gemeinsam, −1 = entgegengesetzt.
- **Nullvektor:** hat keine Richtung; die Funktion gibt 0 zurück, statt durch 0 zu teilen.
- **Query vs. Document:** Voyage bettet Anfrage und Chunks unterschiedlich ein (`input_type`), deshalb zwei Aufrufe.
- Vektoren verschiedener Modelle sind nicht vergleichbar; ein Modellwechsel heißt neu einbetten.

## Formel

```
cos(a, b) = (a · b) / (‖a‖ · ‖b‖)
a · b = Summe a[i] · b[i]          ‖a‖ = Wurzel(Summe a[i]²)
```

## Mini-Beispiel

Test `test_cosine_hand_calculated`, a = (1, 2, 2), b = (2, 0, 1):

| Schritt | Rechnung | Ergebnis |
|---|---|---|
| Skalarprodukt | 1·2 + 2·0 + 2·1 | 4 |
| ‖a‖ | Wurzel(1 + 4 + 4) | 3 |
| ‖b‖ | Wurzel(4 + 0 + 1) | ≈ 2,236 |
| cos | 4 / (3 · 2,236) | **0,596** |

(1, 2) und (2, 4) haben Cosinus 1: gleiche Richtung, andere Länge.

## Komplexität

Ein Cosinus O(d), d = 1024. Alle Kandidaten O(m · d). Einbetten: ein API-Aufruf für alle Texte zusammen (bis 1.000 Texte pro Aufruf).

## Im Projekt

- `src/vector_search/vector_search.py`: `cosine_similarity`, `most_similar`, `Embedder` (ABC), `VoyageEmbedder`.
- **ADR 0001:** Embeddings über eine API statt lokal (kein Modell, keine Rechenlast auf dem Server; dafür Kosten, Schlüssel, Abhängigkeit). Anbieter Voyage AI, Modell `voyage-4`, 1024 Dimensionen, Schlüssel aus `VOYAGE_API_KEY`.
- Auswahl nach Freikontingent (200 Mio. Tokens laut Doku für die Modellreihe 3, für `voyage-4` im Dashboard zu prüfen); grob 10.000 Tokens pro Anfrage.
- R9: Frage einbetten, wenn vorhanden, sonst die Schlagwörter. R6: ohne Schlüssel nur BM25. R10: `EmbeddingError` → nur BM25 mit Hinweis „Vektorsuche nicht verfügbar, nur BM25“.
- R16: Chunk-Vektoren werden in `chunk_embeddings` gespeichert und über den Chunk-Text wiederverwendet (C12).

## Typische Prüferfragen

- **Warum Cosinus und nicht euklidischer Abstand?** Cosinus vergleicht nur die Richtung; die Länge eines Vektors spielt für die Bedeutung keine Rolle.
- **Warum über eine API?** Der Server soll kein Modell laden und rechnen müssen (ADR 0001).
- **Was passiert, wenn Voyage ausfällt?** Kein Absturz: Ergebnis aus BM25 plus Hinweis (R10, Test F5).
- **Warum werden Vektoren in Python verglichen, nicht mit pgvector?** E28: `real[]` reicht bei rund 50 Kandidaten; die getestete Logik bleibt in Python.

## Stolperfallen

- Der Fallback auf BM25 ist still; der Hinweis in `warnings` ist das einzige Signal (L7).
- Kein automatisches Wiederholen bei HTTP 429.
