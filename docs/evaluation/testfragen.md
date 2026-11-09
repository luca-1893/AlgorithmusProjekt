# Testfragen für die Messläufe

Grundlage für die KPI-Messung (Karte #6 und #7): Jede Frage wird mit allen drei Varianten beantwortet, und jeder Lauf landet als Zeile in `runs` (siehe `docs/storage/schema-entwurf.md`).

| Variante | Was passiert |
|---|---|
| `agent_websearch` | Der Agent bekommt nur die Frage und recherchiert mit seiner eingebauten Websuche, ohne `research_papers`. |
| `bm25` | Der Agent nutzt `research_papers`, die Pipeline läuft ohne Einbetter. |
| `hybrid` | Der Agent nutzt `research_papers` mit Voyage (BM25, Vektorsuche, RRF, MMR). |

## Wann eine Frage taugt

1. **Eine eindeutige Quelle:** Die Antwort steht in genau einem arXiv-Paper, dessen ID wir kennen. „Richtige Quelle gefunden“ heißt: Diese arXiv-ID steht unter den Quellen der Antwort.
2. **Nachprüfbar:** Die Stelle ist notiert (Abstract oder Abschnitt im Volltext), dazu eine kurze Referenzantwort.
3. **Nicht aus dem Gedächtnis beantwortbar:** Lieber weniger bekannte Paper. Bei Klassikern wie „Attention Is All You Need“ antwortet ein Modell ohne Recherche, und die Messung zeigt dann nichts.
4. **Titel nicht abschreiben:** Die Frage soll das Thema beschreiben, nicht die Wörter des Titels wiederholen, sonst ist die Suche trivial.
5. **Mischung:**
   - etwa die Hälfte mit Antwort nur im **Volltext**, nicht im Abstract (das prüft den Volltext-Weg)
   - deutsche und englische Fragen (Abstracts sind englisch)
   - verschiedene Fachgebiete, z. B. die acht Anfragen aus `messungen/2026-10-19_review-pr24/`
6. **Umfang:** 20 bis 30 Fragen. Weniger ergibt keine belastbare Trefferquote, mehr kostet zu viele Tokens.

## Was der Mess-Agent pro Lauf liefern muss

Damit ein Lauf in `runs` gespeichert werden kann (`insert_run.sql`):

| Spalte | Woher |
|---|---|
| `run_at` | Startzeitpunkt beim Senden des Prompts (von Python) |
| `variant` | `agent_websearch`, `bm25` oder `hybrid` |
| `keywords` | die Schlagwörter, mit denen der Agent `research_papers` aufgerufen hat; bei `agent_websearch` leer (`NULL`) |
| `question` | die Frage aus dieser Liste, wörtlich |
| `k` | das `k` des Tool-Aufrufs; bei `agent_websearch` leer (`NULL`) |
| `input_tokens`, `output_tokens` | exakte Werte aus der API-Antwort, über alle Schritte des Agenten summiert |
| `duration_ms` | vom Senden des Prompts bis zur fertigen Antwort |
| `found_source` | erst leer; wird danach bewertet, ob die erwartete arXiv-ID unter den Quellen steht |

Gleiches Modell und gleicher System-Prompt für alle drei Varianten, sonst sind die Zahlen nicht vergleichbar.

## Fragen

Felder: **Nr.**, **Frage**, **Sprache**, **erwartete Quelle** (arXiv-ID ohne Version), **Fundstelle**, **Referenzantwort**, **Anmerkung**.

### Format-Beispiele

Die drei Beispiele sind gegen die arXiv-API geprüft (Titel, ID, Abstract). Die ersten beiden verletzen absichtlich Kriterium 3 und zeigen nur das Format; für die Messung durch weniger bekannte Paper ersetzen.

| Nr. | Frage | Sprache | erwartete Quelle | Fundstelle | Referenzantwort | Anmerkung |
|---|---|---|---|---|---|---|
| B1 | Welchen BLEU-Wert erreichte die erste rein aufmerksamkeitsbasierte Übersetzungsarchitektur auf der WMT-2014-Aufgabe Englisch–Deutsch? | de | 1706.03762 | Abstract | 28,4 BLEU | zu bekannt (Kriterium 3) |
| B2 | Which two kinds of memory does retrieval-augmented generation combine for knowledge-intensive tasks? | en | 2005.11401 | Abstract | parametrisch (vortrainiertes seq2seq-Modell) und nicht-parametrisch (dichter Vektorindex über Wikipedia) | zu bekannt (Kriterium 3) |
| B3 | Welche Arbeitsgruppe arbeitete Ende der 1990er an einer präzisen Semantik für UML-Klassendiagramme? | de | 1409.6928 | Abstract | die Precise UML Group (PUML) | Achtung: 1409.6919 trägt dieselbe DOI; als Treffer zählen, wenn beide gelten sollen, vorher festlegen |

### Messfragen

| Nr. | Frage | Sprache | erwartete Quelle | Fundstelle | Referenzantwort | Anmerkung |
|---|---|---|---|---|---|---|
| F01 | | | | | | |
