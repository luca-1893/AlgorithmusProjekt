# 10 Gesamtpipeline und Entscheidungsregeln R1–R16

**In einem Satz:** `research()` verbindet alle Bausteine in fester Reihenfolge, und 16 Entscheidungsregeln legen fest, was bei jeder Verzweigung passiert, von ungültiger Eingabe bis zum Cache-Treffer.

## Kernidee

- Start: Ein MCP-Client ruft `research_papers` mit mindestens einem Schlagwort auf.
- Ende: **Erfolg** (bis zu k Abschnitte als JSON), **keine Treffer** (R4, R5, R7: leere Liste mit Hinweis) oder **Fehler** (R1, R2: Meldung an das Modell, Server läuft weiter).
- **Fail open:** Voyage oder Datenbank fallen aus → Recherche geht mit Hinweis weiter. Nur ungültige Eingabe und unerreichbare Quelle sind Fehler.
- Zwei Schleifen: S1 über alle Dokumente (Chunking), S2 über die Kandidaten (MMR, bis k gewählt).
- Deterministisch: kein Zufall, Gleichstand nach Position bzw. ID (R12).

## Ablauf

```
R1 prüfen → Schlagwörter normalisieren
R13/R15 Cache fragen → sonst R2/R3 arXiv (max_dokumente = 20) → R14 speichern
R4 keine Dokumente? → S1 Chunks (200/40) → R5 keine Chunks?
Index + top_m (m = 50) → R6 kein Einbetter? → nur BM25 (R7)
R8 Kandidaten → R9/R10/R16 einbetten → Cosinus-Rangliste
RRF (k_rrf = 60) → normalisieren → S2 MMR (λ = 0,7) → k Treffer
```

## Regeln (Kurzform)

| R | Bedingung → Folge |
|---|---|
| R1 | Schlagwörter leer oder k nicht 1–20 → Fehler „Ungültige Eingabe“ |
| R2 | Quelle nicht erreichbar / Antwort ungültig → Fehler |
| R3 | „nur begutachtet“ → dreimal so viele holen, ohne Zeitschriftenverweis und DOI verwerfen |
| R4 | keine Dokumente → „Keine Treffer“ |
| R5 | kein Chunk entsteht → „Keine verwertbaren Quellen“ |
| R6 | kein Einbetter (kein Schlüssel) → nur BM25 |
| R7 | nur BM25 und kein Chunk enthält ein Schlagwort → „Kein Chunk enthält ein Schlagwort“ |
| R8 | hybrid und BM25 findet etwas → Kandidaten = BM25-Treffer, sonst alle Chunks |
| R9 | Frage vorhanden → Frage einbetten, sonst Schlagwörter |
| R10 | Einbettung scheitert → Hinweis, weiter wie nur BM25 |
| R11 | Anfragewort in keinem Chunk → trägt nichts bei; leere Dokumente übersprungen |
| R12 | Gleichstand → kleinere Position bzw. ID zuerst |
| R13 | gleiche Suche im Cache, jünger als 7 Tage → aus der Datenbank, arXiv nicht fragen |
| R14 | Dokumente kamen von der Quelle → speichern, bekannte aktualisieren |
| R15 | Datenbank nicht erreichbar → ohne Cache weiter, „Cache nicht verfügbar“ |
| R16 | Vektor zum Chunk(-Text) und Modell gespeichert → wiederverwenden |

## Mini-Beispiel

Testdoku N6/N7: Schlagwort „uml“, k = 2, Dokumente zu UML-Klassen, neuronalen Netzen, UML-Sequenzen → nur BM25: `UML class diagrams` (0,618), `UML sequence diagrams` (0,462); hybrid mit Frage „UML class“: dieselben zwei. F5: Einbetter wirft → BM25-Ergebnis plus „Vektorsuche nicht verfügbar, nur BM25“.

## Komplexität

Dominiert von Netzwerk (ein arXiv-Aufruf, zwei Voyage-Aufrufe). Lokal O(T) für Chunking und Index, Rest siehe Karte 19.

## Im Projekt

- `src/pipeline/pipeline.py`: `research`, `_select`, `_bm25_only`, `_hybrid`; Werte in `PipelineConfig`.
- Regeln und Flowchart: `Phase2/Pseudocode.md`, `Phase2/Flowchart_RAG-Pipeline.drawio`. Regel-IDs stehen in Docstrings und Tests.
- Hinweise von Quelle (Cache) und Einbetter werden in `warnings` angehängt.

## Typische Prüferfragen

- **Warum ist ein Voyage-Ausfall kein Fehler?** Die Recherche soll nicht scheitern; BM25 liefert weiter Ergebnisse (R10).
- **Was passiert, wenn BM25 nichts findet, aber ein Einbetter da ist?** Alle Chunks werden Kandidaten, nur die Vektorsuche entscheidet (R8).
- **Wo ist die Pipeline erweiterbar?** `Source` und `Embedder` sind ABCs; neue Anbieter erben, `research()` bleibt unverändert.
- **Welche Werte sind gemessen?** Nur `overlap = 40`; `k_rrf = 60` ist Literatur, der Rest gesetzt (A11).

## Stolperfallen

- Score im JSON: im BM25-Pfad der BM25-Score, im hybriden Pfad der RRF-Score; nicht vergleichbar.
- R6 (kein Schlüssel) und R10 (Fehler beim Einbetten) nicht verwechseln.
