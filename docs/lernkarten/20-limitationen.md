# 20 Limitationen L1–L10 kurz

**In einem Satz:** Die wichtigsten Grenzen des Prototyps hängen an zwei Annahmen, nur Titel und Abstract (A1) und IDF über den Treffersatz (A5); dazu kommen Messlücken und externe Abhängigkeiten.

## Kernidee

- Jede Limitation in `Phase5/Reflexion.md` folgt dem Schema: Was, Beleg, Warum, Bedeutung, Heute, Lösung.
- Vorschlag für den Pitch (fünf Punkte): **L2, L1, L3, L6, L7**.
- Ehrlich bleiben: dokumentiert ist nicht gelöst; gemessen ist nicht geschätzt.

## Überblick

| Nr. | Limitation | Kern | Lösung / Status |
|---|---|---|---|
| L1 | BM25-Vorauswahl greift auf Abstracts kaum | 20 Abstracts → 22–29 Chunks < m = 50; nur ≈ 10 % aussortiert (21 von 207) | Volltext + Cache; mit Volltext 90–96 % aussortiert |
| L2 | IDF hängt am Treffersatz | Hauptschlagwort in 81–92 % der Chunks, `uml` IDF 0,10 (Volltext 0,62) | IDF über alle gespeicherten Chunks |
| L3 | Antworten nur im Volltext werden nicht gefunden | Volltext ohne Cache ≈ 3,5 min pro Aufruf | `pypdf`, Wiederholen bei 429, Cache; Schema ist vorbereitet (`full_text`, `origin`) |
| L4 | Deutsche Schlagwörter finden kaum etwas | arXiv englisch; Vektorsuche wirkt erst nach der arXiv-Suche | offen; Tool verlangt englische Begriffe |
| L5 | Token-Ersparnis nur geschätzt | Prototyp: ≈ 5.660 → 1.951 Tokens, rund 66 % | Messläufe (laufen noch) |
| L6 | Halluzinationen nur indirekt | `found_source` = belegbar, nicht richtig | bewusste Entscheidung (E33) |
| L7 | Abhängigkeit von arXiv und Voyage | stiller Rückfall auf BM25, kein Wiederholen bei 429 | Fehlerpfade getestet; Cache R13–R16 umgesetzt |
| L8 | Wörter statt Tokens, zerrissene Sätze, Redundanz | overlap = 40: 95,4 % der relevanten Sätze ganz, 6,7 % doppelte Wörter | Nachbar-Treffer zusammenfassen, Satzgrenzen |
| L9 | Parameter nicht für arXiv kalibriert | nur `overlap` gemessen, `k_rrf` Literatur, Rest gesetzt | kleines Raster mit den Messfragen, z. B. λ ∈ {0,5; 0,7; 0,9} |
| L10 | Kleinere Grenzen | keine Seitenzahl, HTTP ohne Anmeldung, Index pro Aufruf, Testabdeckung, nur eine Quelle | dokumentiert |

## Mini-Beispiel

L2 in einem Satz für den Pitch: „Die Formel ist richtig, aber der Korpus ist falsch: arXiv liefert genau die Paper mit dem Schlagwort, also steht es fast überall und zählt fast nichts.“ Bei „quantum error correction“ liegen alle drei Terme bei 0,10 bis 0,14, bei 100 Dokumenten bei 0,04 bis 0,06.

## Im Projekt

- `Phase5/Reflexion.md` (L1–L10, Annahmen A1–A11), ADR 0004 (L1, L2), `messungen/2026-10-19_review-pr24/` (8 echte arXiv-Anfragen, je 20 Dokumente).
- Problematischste Annahme: A5 (IDF über den Treffersatz) → L2; A1 → L1 und L3; A10 → L6; A11 → L9.

## Typische Prüferfragen

- **Warum nicht einfach mehr Dokumente holen?** Dann schneidet m wieder ab, aber L2 wird schlimmer (`quantum` 0,04 bei 100 Dokumenten).
- **Warum kein Volltext im Prototyp?** Bis zu zwei Downloads pro Paper mit Pause, ohne Cache ≈ 3,5 Minuten pro Tool-Aufruf.
- **Was ist die größte Schwäche?** L2, weil sie BM25 auf dem aktuellen Korpus nach Nebenbegriffen ranken lässt.
- **Was würden Sie als Nächstes bauen?** Laut ADR 0004 in dieser Reihenfolge: Cache (erledigt), Volltext mit `pypdf`, IDF über die Datenbank.

## Stolperfallen

- Limitationen L1–L10 nicht mit Leitfragen L1–L6 der Evaluation verwechseln.
- L5 und L6 erst nach den Messläufen mit Zahlen füllen; bis dahin keine Ergebnisse behaupten.
