# Vektorsuche und MMR – Formelsammlung

## 1. Symbole

| Symbol | Bedeutung | Beispiel |
|---|---|---|
| `a`, `b` | Vektoren gleicher Länge (Embeddings) | `a = (1, 2, 2)` |
| `d` | Vektorlänge (Anzahl Zahlen pro Vektor) | 3 |
| `a · b` | Skalarprodukt: Summe der paarweisen Produkte | `1·2 + 2·0 + 2·1 = 4` |
| `‖a‖` | Betrag: Wurzel aus der Summe der Quadrate | `‖(1, 2, 2)‖ = 3` |
| `n` | Anzahl Kandidaten | |
| `k` | Anzahl gewünschter Treffer | |
| `rel(p)` | Relevanz von Kandidat p, zwischen 0 und 1 | |
| `λ` | Gewicht Relevanz gegen Vielfalt, zwischen 0 und 1 | 0.7 |

## 2. Cosinus-Ähnlichkeit

```
cos(a, b) =    a · b
            ─────────
            ‖a‖ · ‖b‖
```

Rechenbeispiel (Test `test_cosine_hand_calculated`):

| Schritt | Rechnung | Ergebnis |
|---|---|---|
| Skalarprodukt | `1·2 + 2·0 + 2·1` | 4 |
| `‖a‖` | `√(1 + 4 + 4)` | 3 |
| `‖b‖` | `√(4 + 0 + 1)` | √5 ≈ 2.236 |
| cos | `4 / (3 · 2.236)` | **0.596** |

| Wert | Bedeutung |
|---|---|
| 1 | gleiche Richtung, auch bei verschiedener Länge: `(1, 2)` und `(2, 4)` |
| 0 | rechtwinklig, nichts gemeinsam |
| −1 | entgegengesetzt |
| Nullvektor | keine Richtung, wir geben **0** zurück statt durch 0 zu teilen |

## 3. Top-k mit begrenztem Min-Heap

| Variante | Laufzeit | Speicher |
|---|---|---|
| Alles sortieren, die ersten k nehmen | O(n · log n) | O(n) |
| **Min-Heap mit höchstens k Einträgen** | O(n · log k) | O(k) |

Der Heap hält immer die k besten bisher gesehenen Werte, der schwächste liegt oben. Ein neuer Wert verdrängt ihn nur, wenn er besser ist. Gleichstand: Eintrag `(score, −position)`, dadurch gilt die größere Position als schwächer und fliegt zuerst raus.

## 4. MMR (Maximal Marginal Relevance)

```
MMR(p) = λ · rel(p) − (1 − λ) · max  cos(v_p, v_s)
                               s ∈ Auswahl
```

Ausgewählt wird in jeder Runde der Kandidat mit dem höchsten MMR-Wert. Ist die Auswahl leer, ist der zweite Teil 0.

Rechenbeispiel (Test `test_mmr_skips_near_duplicate`, λ = 0.5, k = 2):

| Kandidat | Vektor | rel |
|---|---|---|
| 0 | (1, 0) | 1.00 |
| 1 | (1, 0.01) | 0.95 |
| 2 | (0, 1) | 0.60 |

| Runde | Kandidat | Rechnung | MMR |
|---|---|---|---|
| 1 | 0 | `0.5 · 1.00 − 0.5 · 0` | **0.500** ← gewählt |
| 1 | 1 | `0.5 · 0.95 − 0.5 · 0` | 0.475 |
| 1 | 2 | `0.5 · 0.60 − 0.5 · 0` | 0.300 |
| 2 | 1 | `0.5 · 0.95 − 0.5 · cos((1, 0.01), (1, 0)) = 0.475 − 0.5 · 0.99995` | −0.025 |
| 2 | 2 | `0.5 · 0.60 − 0.5 · cos((0, 1), (1, 0)) = 0.300 − 0` | **0.300** ← gewählt |

Ergebnis: `[0, 2]`. Kandidat 1 ist fast dasselbe wie Kandidat 0 und fällt trotz höherer Relevanz raus.

## 5. Was λ bewirkt

| λ | Effekt |
|---|---|
| 1 | nur Relevanz, MMR ist dann einfach Top-k |
| 0.7 | Standard in diesem Projekt: Relevanz überwiegt, Duplikate werden bestraft |
| 0.5 | Relevanz und Vielfalt gleich gewichtet |
| 0 | nur Vielfalt; selbst die erste Wahl ignoriert die Relevanz, bei Gleichstand gewinnt die kleinere Position |

## 6. Plausibilitäts-Checks

- Die Cosinus-Ähnlichkeit liegt immer zwischen −1 und 1 und ist symmetrisch: `cos(a, b) = cos(b, a)`.
- Top-k liefert genau `min(k, n)` Einträge, absteigend sortiert.
- MMR wählt jede Position höchstens einmal und bei λ > 0 als Erstes immer den relevantesten Kandidaten.
- `rel` muss zwischen 0 und 1 liegen, sonst ist die Abwägung gegen die Ähnlichkeit verzerrt. Dafür gibt es `normalize_scores` im Ranking.
