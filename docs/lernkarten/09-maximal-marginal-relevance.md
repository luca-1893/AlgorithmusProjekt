# 09 Maximal Marginal Relevance (MMR)

**In einem Satz:** MMR wählt die endgültigen k Abschnitte schrittweise so aus, dass jeder relevant ist, aber nicht fast dasselbe sagt wie ein schon gewählter.

## Kernidee

- Greedy: in jeder Runde den Kandidaten mit dem höchsten MMR-Wert nehmen und aus den übrigen streichen.
- Belohnung: normierte Relevanz (aus RRF). Strafe: höchste Cosinus-Ähnlichkeit zu einem schon gewählten Chunk.
- **λ** wägt ab: 1 = nur Relevanz (einfach Top-k), 0,7 = Relevanz überwiegt, Duplikate werden bestraft, 0,5 = gleich gewichtet, 0 = nur Vielfalt.
- Ist die Auswahl leer, ist die Strafe 0; bei λ > 0 wird zuerst immer der relevanteste gewählt.
- Gleichstand: kleinere Position (R12). Jede Position höchstens einmal.

## Formel / Ablauf

```
MMR(p) = λ · rel(p) − (1 − λ) · max über s in Auswahl von cos(v_p, v_s)

SOLANGE Kandidaten übrig UND Anzahl(Auswahl) < k:
    bester = Kandidat mit höchstem MMR
    Auswahl.anhängen(bester); aus übrigen entfernen
    für jeden übrigen: max_ähnlichkeit = max(alt, cos(v, v_bester))
```

## Mini-Beispiel

Test `test_mmr_skips_near_duplicate`, λ = 0,5, k = 2; Kandidaten 0: (1, 0), rel 1,00; 1: (1; 0,01), rel 0,95; 2: (0, 1), rel 0,60.

| Runde | Kandidat | Rechnung | MMR |
|---|---|---|---|
| 1 | 0 | 0,5 · 1,00 − 0 | **0,500** gewählt |
| 1 | 1 | 0,5 · 0,95 − 0 | 0,475 |
| 1 | 2 | 0,5 · 0,60 − 0 | 0,300 |
| 2 | 1 | 0,475 − 0,5 · 0,99995 | −0,025 |
| 2 | 2 | 0,300 − 0,5 · 0 | **0,300** gewählt |

Ergebnis `[0, 2]`: Kandidat 1 ist fast ein Duplikat von 0 und fällt trotz höherer Relevanz raus.

## Komplexität

O(k · m · d): k Runden, je bis zu m Kandidaten, je ein Cosinus der Länge d. Die höchste Ähnlichkeit pro Kandidat wird nach jeder Wahl nur mit dem **neuen** Vektor aktualisiert, nicht mit der ganzen Auswahl.

## Im Projekt

- `src/vector_search/vector_search.py` → `mmr_select(relevance, vectors, k, lambda_=0.7)`.
- Schleife S2 der Pipeline; `λ = 0.7` (`PipelineConfig.mmr_lambda`), gesetzt, nicht kalibriert (L9). Bei m = 50 und kleinem k unkritisch.
- Eingaben: normierte RRF-Scores (Karte 08) und die Kandidatenvektoren in Fusions-Reihenfolge.

## Typische Prüferfragen

- **Warum MMR statt einfach die k besten?** Benachbarte, überlappende Chunks oder zwei Fassungen eines Papers würden sonst Plätze und Tokens doppelt belegen.
- **Was passiert bei λ = 1?** MMR ist dann reines Top-k nach Relevanz.
- **Warum ist das greedy und nicht optimal?** Die beste Teilmenge zu finden wäre kombinatorisch teuer; die schrittweise Wahl ist O(k · m · d).
- **Warum muss rel zwischen 0 und 1 liegen?** Sonst passt die Größenordnung nicht zur Cosinus-Ähnlichkeit.

## Stolperfallen

- Mit λ = 0,7 ist die Strafe nur 0,3 · Ähnlichkeit; Fast-Duplikate können durchrutschen (L8).
- `λ` außerhalb 0 bis 1 oder `k ≤ 0` → `ValueError` (Test F8).
