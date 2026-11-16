# Ranking – Formelsammlung

## 1. Symbole

| Symbol | Bedeutung | Beispiel |
|---|---|---|
| `R` | Menge der Ranglisten, z. B. BM25 und Vektorsuche | 2 Listen |
| `rang_r(d)` | Platz von Kandidat d in Rangliste r, beginnt bei 1 | |
| `k_rrf` | Glättungskonstante | 60 |

## 2. Reciprocal Rank Fusion (RRF)

```
RRF(d) =  Σ     1
         r ∈ R ──────────────
               k_rrf + rang_r(d)
```

Kommt d in einer Liste nicht vor, trägt diese Liste nichts bei.

Rechenbeispiel (Test `test_rrf_hand_calculated`, Listen `[1, 2]` und `[2, 3]`, k_rrf = 0):

| Kandidat | Liste 1 | Liste 2 | RRF |
|---|---|---|---|
| 1 | 1 / 1 | – | 1.0 |
| 2 | 1 / 2 | 1 / 1 | **1.5** |
| 3 | – | 1 / 2 | 0.5 |

Ergebnis: `2 > 1 > 3`. Mit k_rrf = 60 werden die Abstände kleiner: 0.0325, 0.0164, 0.0161.

## 3. Warum Ränge statt Rohwerte

| Rohwert | Skala |
|---|---|
| BM25-Score | offen nach oben, hängt von Korpus und Anfrage ab |
| Cosinus-Ähnlichkeit | −1 bis 1 |

Würde man die Rohwerte addieren, entschiede die Skala und nicht die Qualität. Ränge sind in beiden Listen gleich gebaut.

## 4. Was k_rrf bewirkt

| k_rrf | Effekt |
|---|---|
| 0 | Platz 1 zählt doppelt so viel wie Platz 2, die Spitze dominiert |
| 60 | Standardwert aus der Literatur, Abstände zwischen den oberen Plätzen schrumpfen |
| groß | alle Plätze fast gleich, es zählt vor allem, in wie vielen Listen ein Kandidat vorkommt |

## 5. Min-Max-Normalisierung

```
norm(x) =   x − min
          ─────────
          max − min
```

Bildet Scores auf 0 bis 1 ab, damit MMR Relevanz und Ähnlichkeit vergleichen kann. Sind alle Werte gleich, wird jeder zu 1.

## 6. Plausibilitäts-Checks

- Jeder RRF-Score ist größer als 0 und höchstens `|R| / (k_rrf + 1)`.
- Ein Kandidat, der in allen Listen auf Platz 1 steht, ist immer vorne.
- Nach der Normalisierung ist der kleinste Wert 0 und der größte 1, außer alle Werte sind gleich.
