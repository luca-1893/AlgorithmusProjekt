# 08 Score-Normalisierung

**In einem Satz:** Die Min-Max-Normalisierung bildet die RRF-Scores auf 0 bis 1 ab, damit MMR Relevanz und Cosinus-Ähnlichkeit auf derselben Skala gegeneinander abwägen kann.

## Kernidee

- Min-Max: der kleinste Wert wird 0, der größte 1, alles dazwischen linear.
- **Warum nötig:** RRF-Scores liegen bei k_rrf = 60 nur bei etwa 0,016 bis 0,033; die Ähnlichkeit im MMR liegt bei bis zu 1. Ohne Normierung würde der Ähnlichkeitsabzug alles dominieren.
- **Sonderfall:** Sind alle Werte gleich, wird jeder zu 1 (kein Kandidat ist schlechter), statt durch 0 zu teilen.
- Leere Liste → leere Liste.
- Die Reihenfolge bleibt erhalten; nur die Skala ändert sich.

## Formel

```
norm(x) = (x − min) / (max − min)          alle Werte gleich → 1
```

## Mini-Beispiel

- Test `test_normalize_example`: `[2.0, 4.0, 3.0]` → `[0.0, 1.0, 0.5]`.
- Test R7: `[0.3, 0.3]` → `[1.0, 1.0]`.
- RRF-Werte aus Karte 07 (k_rrf = 60): 0,0325 / 0,0164 / 0,0161 → 1 / ≈ 0,016 / 0. Der kleine Abstand zwischen Platz 2 und 3 bleibt klein, Platz 1 wird deutlich abgesetzt.

## Komplexität

O(n): einmal Minimum und Maximum, einmal umrechnen.

## Im Projekt

- `src/ranking/ranking.py` → `normalize_scores(scores)`.
- In `pipeline._hybrid`: `relevance = normalize_scores([score for _, score in fused])`, danach `mmr_select(relevance, ...)`.
- Formelsammlung: `docs/ranking/ranking-formelsammlung.md`, Abschnitt 5; Plausibilitäts-Check in `docs/vector_search/vector_search-formelsammlung.md`: `rel` muss zwischen 0 und 1 liegen, sonst ist die Abwägung verzerrt.
- Im JSON steht weiterhin der **RRF-Score**, nicht der normierte Wert.

## Typische Prüferfragen

- **Warum überhaupt normalisieren?** MMR rechnet `λ · rel − (1 − λ) · Ähnlichkeit`; beide Teile müssen vergleichbar groß sein.
- **Was passiert bei lauter gleichen Scores?** Alle werden 1; Division durch null wird vermieden.
- **Ändert die Normalisierung das Ranking?** Nein, sie ist streng monoton; nur die Abstände werden auf 0 bis 1 gestreckt.
- **Gibt es Alternativen?** Z. B. Division durch das Maximum oder z-Standardisierung (Lehrbuch); Min-Max garantiert genau den Bereich 0 bis 1.

## Stolperfallen

- Der schwächste Kandidat bekommt immer Relevanz 0, auch wenn er absolut kaum schlechter ist; im MMR zählt dann nur noch sein Ähnlichkeitsabzug.
- Min-Max ist empfindlich gegen Ausreißer: ein einzelner sehr hoher Wert staucht alle anderen nach unten.
