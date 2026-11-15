# Klicktest: Messläufe in `runs`

Prüft von Hand, ob das Messskript (`src/evaluation/messlauf.py`) korrekte Zeilen in die Tabelle `runs` der Arbeits-Datenbank `algorithmusprojekt` schreibt. Der Probelauf ruft weder die Claude API noch arXiv auf, kostet also nichts und braucht keinen `ANTHROPIC_API_KEY`.

## Vorbereitung

1. PostgreSQL läuft (`brew services list`, Eintrag `postgresql@18` ist `started`).
2. In DataGrip die Verbindung zu `algorithmusprojekt` öffnen, Schema `public`, Tabelle `runs`. Sie sollte vor dem ersten Test leer sein (Stand 15.11.2026: 0 Zeilen).

## Schritte

| Nr. | Aktion | Erwartet |
|---|---|---|
| K1 | Im Terminal aus dem Projektordner: `PYTHONPATH=src .venv/bin/python -m evaluation.messlauf --probe --fragen F01` | drei Zeilen Ausgabe, je eine pro Variante, jeweils „Quelle gefunden“, am Ende der Pfad zum Log |
| K2 | In DataGrip `runs` neu laden (⌘R) | 3 neue Zeilen: `agent_websearch`, `bm25`, `hybrid` |
| K3 | Spalte `question` ansehen | beginnt mit „[Probe] Ein über 300 kg schwerer …“, sonst wörtlich F01 aus `docs/evaluation/testfragen.md` |
| K4 | Spalten `keywords` und `k` | bei `agent_websearch` beide `NULL`; bei `bm25` und `hybrid` `{probe}` und `3` |
| K5 | Spalten `input_tokens`, `output_tokens`, `duration_ms` | 100, 20 und eine kleine Zahl ≥ 0 (der Probelauf zählt feste Werte) |
| K6 | Spalte `found_source` | bei allen drei `true` |
| K7 | Spalte `run_at` | aktuelle Uhrzeit, gleiche Minute bei allen drei |
| K8 | Log öffnen: `messungen/<datum>_messlauf_probe/runs.jsonl` | 3 Zeilen JSON, `run_id` passt zur `id` in DataGrip, `answer` endet mit der arXiv-URL von F01 (2601.11143) |
| K9 | Mehrere Fragen und nur eine Variante: `… --probe --fragen F06,F14 --varianten bm25` | 2 neue Zeilen, beide `bm25` |
| K10 | Auswertung in DataGrip: Inhalt von `sql/kpi_by_variant.sql` ausführen | je Variante eine Zeile; `runs` passt zur Anzahl der Probezeilen, `hit_rate` = 1 |
| K11 | Aufräumen: `DELETE FROM runs WHERE question LIKE '[Probe]%';` und den Ordner `messungen/<datum>_messlauf_probe/` löschen | `runs` wieder leer |

## Echter Lauf (nach dem Klicktest)

Erst eine Frage, dann alle:

```
export ANTHROPIC_API_KEY=…
PYTHONPATH=src .venv/bin/python -m evaluation.messlauf --fragen F21
PYTHONPATH=src .venv/bin/python -m evaluation.messlauf
```

Beim echten Lauf zusätzlich prüfen: `input_tokens` bei `agent_websearch` deutlich größer als bei `bm25` und `hybrid` (Leitfrage L1), `duration_ms` im Bereich von Sekunden, und in `runs.jsonl` die `answer` stichprobenartig gegen die Referenzantwort in `testfragen.md`. Läuft eine Frage auf einen Fehler (z. B. Netzwerk), meldet das Skript ihn und speichert für diesen Lauf nichts; die übrigen laufen weiter.

## Bekannte Grenzen

- `found_source` wird automatisch gesetzt: wahr, wenn die erwartete arXiv-ID irgendwo in der Antwort steht. Nennt das Modell die ID ohne sie als Beleg zu nutzen, zählt das trotzdem als Treffer; deshalb die Stichprobe im Log.
- Ruft das Modell in `bm25` oder `hybrid` das Tool gar nicht auf, wird `keywords = {}` und `k = 5` gespeichert (das Schema verlangt dort einen Wert). Solche Läufe erkennt man im Log an `"tool_calls": []`.
- Ruft es das Tool mehrmals auf, stehen in `runs` die Schlagwörter des **ersten** Aufrufs; alle Aufrufe stehen im Log.
