# BM25 – Formelsammlung

Beispielkorpus (Einkaufszettel):

| Zettel | Inhalt |
|---|---|
| Z1 | apfel apfel banane |
| Z2 | banane milch |
| Z3 | apfel brot milch käse butter |

## 1. Symbole

| Symbol | Bedeutung | Gilt für | Beispiel |
|---|---|---|---|
| `N` | Anzahl Dokumente | Korpus | 3 |
| `avgdl` | durchschnittliche Dokumentlänge | Korpus | 3.33 |
| `\|D\|` | Länge von Dokument D (Wörter) | pro Dokument | \|Z3\| = 5 |
| `n(q)` | in **wie vielen Dokumenten** q vorkommt (Dokumenthäufigkeit) | pro Wort | n(apfel) = 2 |
| `f(q,D)` | **wie oft** q in D vorkommt (Termhäufigkeit) | pro Wort + Dokument | f(apfel, Z1) = 2 |
| `k1` | Sättigung, selbst gewählt | Parameter | 1.5 |
| `b` | Längenbremse, selbst gewählt | Parameter | 0.75 |

## 2. Gesamtformel

```
score(D, Q) = Σ  IDF(q) · f(q,D) · (k1 + 1)
             q∈Q          ─────────────────────────────────────
                          f(q,D) + k1 · (1 − b + b · |D| / avgdl)
```

## 3. Rechenweg (4 Schritte)

| Schritt | Formel | Wie oft rechnen? |
|---|---|---|
| **A** Längenfaktor | `L = \|D\| / avgdl` | 1× pro Dokument |
| **B** Bremse | `K = k1 · (1 − b + b · L)` | 1× pro Dokument |
| **C1** Seltenheit | `IDF(q) = ln( (N − n(q) + 0.5) / (n(q) + 0.5) + 1 )` | 1× pro Anfragewort |
| **C2** Häufigkeit | `TF(q,D) = f(q,D) · (k1 + 1) / (f(q,D) + K)` | pro Wort + Dokument |
| **C3** Beitrag | `IDF(q) · TF(q,D)` | pro Wort + Dokument |
| **D** Score | `score(D,Q) = Summe aller Beiträge` | 1× pro Dokument |

## 4. Was die Teile bedeuten

| Teil | Wert | Bedeutung |
|---|---|---|
| `L` | < 1 | Dokument kürzer als der Durchschnitt, Treffer zählen **mehr** |
| | = 1 | Durchschnitt, keine Korrektur |
| | > 1 | länger als der Durchschnitt, Treffer zählen **weniger** |
| `K` | klein | wenig Bremse |
| | groß | viel Bremse |
| `TF` | f = 0 | **0**, das Wort trägt nichts bei |
| | f → ∞ | geht gegen **k1 + 1**, die Obergrenze |
| `IDF` | n(q) klein | großes Gewicht, seltenes Wort |
| | n(q) = N | kleines Gewicht, das Wort steht überall |

## 5. Was passiert, wenn man an den Parametern dreht

| Einstellung | Effekt |
|---|---|
| `k1 = 0` | TF ist immer 1, nur noch „kommt vor / kommt nicht vor“ |
| `k1` groß (z. B. 3) | Häufigkeit zählt lange mit, kaum Sättigung |
| `b = 0` | K = k1, die Länge ist komplett egal |
| `b = 1` | volle Längenkorrektur, K = k1 · L |
| Standard | `k1 = 1.2 … 2.0`, `b = 0.75` |

## 6. IDF-Varianten

| Variante | Formel | Problem |
|---|---|---|
| Klassisch (Robertson) | `ln( (N − n + 0.5) / (n + 0.5) )` | wird **negativ**, wenn das Wort in mehr als der Hälfte der Dokumente steht |
| Mit +1 (Lucene) | `ln( (N − n + 0.5) / (n + 0.5) + 1 )` | immer > 0, die verwenden wir |

## 7. Plausibilitäts-Checks

- Ein Score ist nie negativ (mit der +1-IDF).
- Ein Dokument ohne Anfragewort hat den Score **0**.
- Ein TF-Teil ist immer kleiner als `k1 + 1`.
- K ist für alle Wörter im selben Dokument gleich.
- Kommt ein Dokument dazu, ändern sich `N` und `avgdl` und damit potenziell die IDF **jedes** Wortes.
