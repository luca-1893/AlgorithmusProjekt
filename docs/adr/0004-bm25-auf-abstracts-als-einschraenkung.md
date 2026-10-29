# ADR 0004: BM25 auf Abstracts – Vorauswahl und IDF als dokumentierte Einschränkung

- **Status:** angenommen
- **Datum:** 2026-10-19
- **Entschieden von:** Luca, in Abstimmung mit dem Dozenten

## Kontext

Das Review von PR #24 hat zwei Schwächen in der Verbindung von BM25 und Pipeline gemessen; die lokale Wiederholung bestätigt die Zahlen exakt (`messungen/2026-10-19_review-pr24/`).

**1. Die BM25-Vorauswahl filtert auf Abstracts kaum etwas.** 20 Dokumente ergeben nur 22 bis 29 Chunks, also weniger als `candidates_m = 50`. `top_m` behält deshalb jeden Chunk, der überhaupt ein Schlagwort enthält; aussortiert werden nur rund 10 %. Im hybriden Pfad gehen damit fast alle Chunks an Voyage.

**2. Die IDF wird nur über den Treffersatz berechnet.** arXiv liefert die Dokumente gerade wegen der Schlagwörter. Das Hauptschlagwort steht deshalb in fast jedem Chunk, seine IDF geht gegen null (`uml` 0,10, `quantum` bei 50 Dokumenten 0,04). Den BM25-Score bestimmen die Nebenbegriffe.

Mit Volltext statt Abstract sieht es anders aus (gleiche 8 Anfragen, 20 Dokumente):

| | Abstract | Volltext |
|---|---|---|
| Chunks | 22–29 pro Anfrage | 515–1.167 pro Anfrage |
| von der Vorauswahl aussortiert | ≈ 10 % | 90–96 % |
| IDF des Hauptbegriffs, z. B. `uml` | 0,10 | 0,62 |

Volltext braucht aber pro Paper bis zu zwei Downloads mit Pause dazwischen, ohne Cache etwa 3,5 Minuten pro Tool-Aufruf.

## Entscheidung

Für den Prototyp bleibt es bei Titel und Abstract. Beide Schwächen werden als Einschränkung dokumentiert, nicht als Bug behoben:

- BM25 ist auf Abstracts vor allem ein **Ranking-Signal** für die Rangfusion und sortiert nur Chunks ganz ohne Schlagwort aus. Die eigentliche Vorauswahl greift erst mit Volltext.
- BM25 rankt innerhalb des Treffersatzes nach **seltenen Nebenbegriffen**; das Hauptschlagwort zählt kaum.

## Betrachtete Alternativen

| Alternative | Wirkung | Warum nicht jetzt |
|---|---|---|
| `max_documents` auf 50–100, `candidates_m` an k koppeln (z. B. 3 · k) | Vorauswahl schneidet wieder ab | Problem 2 wird bei mehr Dokumenten eher schlimmer (`quantum` 0,04 bei 100) |
| Volltext ohne Cache | löst Problem 1, entschärft Problem 2 | 3,5 Minuten pro Aufruf |
| **Volltext mit Datenbank-Cache** | wie oben, jedes Paper kostet nur beim ersten Abruf | hängt am SQL (Karte #20), **geplant** |
| **IDF über alle gespeicherten Chunks** | löst Problem 2 grundsätzlich | braucht den Cache; `top_m` muss dafür eine fertige IDF-Tabelle annehmen, **geplant** |

## Konsequenzen

- Pseudocode, Flowchart und README nennen beide Einschränkungen.
- Die Reflexion (Phase 5) führt sie als Limitationen mit den Messwerten auf.
- Nach dem SQL folgen in dieser Reihenfolge: Cache, Volltext mit `pypdf` (gleich gut wie `pymupdf4llm`, siebenmal schneller, BSD-Lizenz), IDF über die Datenbank.
- Der Volltext-Abruf braucht ein Wiederholen mit wachsender Wartezeit, weil arXiv auch bei 3,1 s Abstand mit HTTP 429 drosselt.
- `overlap = 40` bleibt (siehe `docs/chunking/chunking-pseudocode.md`). Benachbarte Treffer im Ergebnis zu einem Abschnitt zusammenzufassen, ist als eigene Änderung vorgemerkt: Schon ohne Overlap hat fast die Hälfte der Top-50-Chunks ihren Nachbarn ebenfalls in der Auswahl.
