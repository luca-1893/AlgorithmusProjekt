# 17 Evaluation und KPIs

**In einem Satz:** 25 Messfragen mit bekannter arXiv-Quelle werden je in drei Varianten von Claude beantwortet; gespeichert werden Tokens, Dauer und ob die erwartete Quelle in der Antwort steht.

## Kernidee

- **Varianten:** `agent_websearch` (Websuche des Modells, ohne Tool), `bm25` (Tool ohne Einbetter), `hybrid` (Tool mit Voyage, RRF, MMR).
- **Gleich für alle:** gleiches Modell, gleicher System-Prompt, ohne Cache.
- **KPIs je Lauf:** `input_tokens`, `output_tokens` (exakt aus der API, über alle Schritte summiert), `duration_ms` (vom Senden bis zur Antwort), `found_source`.
- **found_source:** wahr, wenn die erwartete arXiv-ID (mit oder ohne Version) in der Antwort steht; Näherung für „belegte Antwort“, kein Halluzinationsmaß (E33, L6).
- **Fragenmix:** F01–F13 Fundstelle im Volltext, F14–F25 im Abstract; 13 deutsch, 12 englisch; überwiegend Paper aus 2025/2026, damit das Modell sie nicht aus dem Gedächtnis kennt.
- Erfolgskriterien sind **vorher** festzulegen, nicht nach der Messung.

## Formel / Ablauf

```
FÜR jede Frage F01..F25, FÜR jede Variante:
    run_at = Startzeit; Claude beantwortet die Frage (Tool-Runner, max. 10 Schritte)
    Tokens summieren; found_source = erwartete ID in ARXIV_ID.findall(antwort)
    save_run → runs; rate_run(found_source); Zeile in messungen/<datum>_messlauf/runs.jsonl
Trefferquote = Anzahl found_source = true / Anzahl bewerteter Läufe     (kpi_by_variant.sql)
```

## Leitfragen (Auswahl)

| Nr. | Frage | Vorschlag Erfolgskriterium |
|---|---|---|
| L1 | Spart das Tool Tokens gegenüber `agent_websearch`? | mindestens 50 % weniger Input-Tokens |
| L2 | Findet es die Quelle mindestens so oft? | Trefferquote mit Tool nicht schlechter |
| L3 | Lohnt sich `hybrid` gegenüber `bm25`? | trifft öfter, Aufschlag unter wenigen Sekunden |
| L5 | Unterschied deutsch/englisch? | kein Einbruch bei deutschen Fragen |
| L6 | Hilft Volltext? | braucht zwei Tool-Versionen |

## Mini-Beispiel

F21: erwartete Quelle 2608.00452, Referenzantwort „von 0,32 auf 0,47“, Fundstelle Abstract. Steht in der Antwort `arxiv.org/abs/2608.00452v1`, gilt `found_source = true`.

## Im Projekt

- `src/evaluation/messlauf.py` (`MODEL = "claude-opus-5-5"`, `DEFAULT_K = 5`, `ARXIV_PAUSE_S = 3.0`), Fragen `docs/evaluation/testfragen.md`, Leitfragen `docs/evaluation/leitfragen.md`, Auswertung `sql/kpi_by_variant.sql`, Tabelle `runs`.
- `--probe`: ohne API und arXiv, Fragen mit Präfix „[Probe]“; `--fragen F01,F14` für einzelne Fragen. Der volle Lauf kostet API-Guthaben.
- **Stand:** Die Messläufe stehen noch aus; es gibt noch keine Ergebnisse zu Tokens oder Trefferquote.

## Typische Prüferfragen

- **Wie messen Sie Halluzinationen?** Gar nicht direkt; `found_source` zeigt, dass die Antwort belegbar ist, nicht dass sie richtig ist.
- **Warum ohne Cache?** Sonst misst die Dauer den Datenbankzugriff statt der Recherche.
- **Warum 25 Fragen?** Weniger ergibt keine belastbare Trefferquote, mehr kostet zu viele Tokens (Entscheidung Luca, 15.11.).
- **Warum zählt der Cache der Claude-API zu den Input-Tokens?** Alle Input-Anteile (normal, Cache-Erstellung, Cache-Lesen) werden summiert, damit die Varianten vergleichbar bleiben.

## Stolperfallen

- Leitfragen L1–L6 nicht mit Limitationen L1–L10 verwechseln.
- Teiltreffer (F05, F08, F11) und gerundete Zahlen (F02, F12) vor der Messung regeln.
