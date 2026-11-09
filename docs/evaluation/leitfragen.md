# Leitfragen der Evaluation

Was die Messläufe beantworten sollen. Grundlage ist das Projektziel aus der README: weniger Halluzinationen, weniger Tokens, kürzere Laufzeit. Die Fragen für die Läufe stehen in `testfragen.md`, die Daten in der Tabelle `runs`, die Auswertung macht `kpi_by_variant.sql`.

Die Erfolgskriterien sind **Vorschläge** und müssen vor der Messung festgelegt werden, nicht danach.

| Nr. | Leitfrage | Kennzahl | Vergleich | Erfolgskriterium (Vorschlag) |
|---|---|---|---|---|
| L1 | Spart das Tool Tokens gegenüber der eigenen Websuche des Agenten? | Ø `input_tokens` je Variante | `bm25` und `hybrid` gegen `agent_websearch` | mindestens 50 % weniger Input-Tokens; die Schätzung im Prototyp lag bei 69 % |
| L2 | Findet der Agent mit dem Tool die richtige Quelle mindestens so oft wie ohne? | Trefferquote: Anteil `found_source = true` an den bewerteten Läufen | `bm25` und `hybrid` gegen `agent_websearch` | Trefferquote mit Tool nicht schlechter als ohne |
| L3 | Lohnt sich die Vektorsuche gegenüber BM25 allein? | Trefferquote und Ø `duration_ms` | `hybrid` gegen `bm25` | `hybrid` trifft öfter; der Zeitaufschlag (Voyage) bleibt unter wenigen Sekunden |
| L4 | Wie lange dauert eine Recherche mit Tool? | Ø `duration_ms` | alle drei Varianten | mit Tool nicht langsamer als `agent_websearch` |
| L5 | Ändert sich das Bild zwischen deutschen und englischen Fragen? | L1 und L2 getrennt nach Sprache der Frage | je Variante | kein Einbruch bei deutschen Fragen |
| L6 | Hilft der Volltext gegenüber Titel und Abstract? | Trefferquote bei Fragen mit Fundstelle im Volltext | Volltext-Version gegen Abstract-Version des Tools | bei Volltext-Fragen deutlich höhere Trefferquote |

## Offene Punkte

- **Halluzinationen** misst `runs` nur indirekt über `found_source`. Ob die Antwort selbst stimmt, wird nicht gespeichert. Entscheiden: reicht die richtige Quelle als Näherung, oder braucht `runs` eine zweite Bewertung wie „Antwort korrekt“?
- **L5** braucht die Sprache je Lauf; sie steht in `testfragen.md` und lässt sich über `question` zuordnen, eine eigene Spalte gibt es nicht.
- **L6** braucht zwei Tool-Versionen; geht nur, wenn die Abstract-Version vor dem Umbau auf Volltext gemessen wird.
- **Cache:** Ob ein Lauf aus dem Cache bedient wurde, beeinflusst die Dauer stark, steht aber nicht in `runs`. Entscheiden: Cache für Messläufe abschalten oder als Spalte erfassen.
- Gleiches Modell, gleicher System-Prompt und gleiches `k` für alle Varianten, sonst sind die Zahlen nicht vergleichbar.
