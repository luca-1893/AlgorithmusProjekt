# Messungen zum Review von PR #24 (19.10.2026)

Lokale Wiederholung der Messungen aus den Review-Kommentaren an PR #24, auf Commit `41787b9`. Die Skripte stammen aus den Kommentaren; ergänzt ist nur die Liste der acht Anfragen, wo dort `QUERIES = [...]` stand.

## Ausführen

Aus dem Repo-Root, in einer eigenen Umgebung (Python 3.15):

```
python3.15 -m venv messung-venv
messung-venv/bin/pip install -r messungen/2026-10-19_review-pr24/requirements-messung.txt
brew install pandoc
D=messungen/2026-10-19_review-pr24
messung-venv/bin/python $D/messe_vorauswahl.py src $D/ausgaben/ergebnis.json
messung-venv/bin/python $D/messe_volltext.py src cache/ $D/ausgaben/ergebnis_volltext.json
messung-venv/bin/python $D/messe_overlap.py src cache/ 0,10,20,40,60,80,100 200
messung-venv/bin/python $D/messe_extraktion.py src messung_extraktion/ 25
python3 $D/vergleich.py
```

Laufzeit insgesamt etwa 25 Minuten, vor allem wegen der Pausen zwischen den arXiv-Anfragen. `cache/` und `messung_extraktion/` enthalten die heruntergeladenen Texte (zusammen rund 75 MB) und sind nicht im Repo. `pymupdf4llm` 2.0 ist ein leeres Paket; deshalb ist 0.3.4 festgelegt. `docling` fehlt, weil es für Python 3.15 kein PyTorch gibt.

`referenz/` enthält die Ausgaben aus den Review-Kommentaren, `ausgaben/` die lokalen.

## Ergebnisse

### 1. BM25-Vorauswahl auf Abstracts (`messe_vorauswahl.py`)

Alle 24 Werte (8 Anfragen × 20, 50, 100 Dokumente) stimmen exakt mit dem Review überein.

| Dokumente | Chunks | von `top_m` behalten | durch `m = 50` abgeschnitten | IDF des Hauptbegriffs |
|---|---|---|---|---|
| 20 (Standard) | 22–29 | alle mit Schlagwort (≈ 90 %) | 0 | 0,10–0,43 |
| 50 | 61–69 | 50 | 5–12 | 0,04–0,38 |
| 100 | 122–129 | 50 | 59–69 | 0,04–0,41 |

### 2. Abstract gegen Volltext (`messe_volltext.py`, 20 Dokumente)

| Anfrage | Chunks Volltext (Review → lokal) | aussortiert | Paper in den Top 50 |
|---|---|---|---|
| UML, class diagram, semantics | 997 → 995 | 95 % → 95 % | 15 → 15 |
| BM25, information retrieval | 517 → 515 | 90 % → 90 % | 14 → 13 |
| retrieval augmented generation, hallucination | 951 → 936 | 95 % → 95 % | 13 → 13 |
| transformer, attention | 890 → 878 | 94 % → 94 % | 15 → 15 |
| graph neural network, molecule | 1.031 → 1.028 | 95 % → 95 % | 13 → 13 |
| reinforcement learning, robotics, sim-to-real | 799 → 800 | 94 % → 94 % | 14 → 14 |
| quantum error correction | 1.179 → 1.167 | 96 % → 96 % | 15 → 15 |
| federated learning, privacy, differential privacy | 813 → 816 | 94 % → 94 % | 14 → 14 |

Abweichungen kommen aus den Quellen: Bei zwei Anfragen gab es lokal ein Paper mehr als HTML statt PDF, und die `pypdf`-Version unterscheidet sich.

### 3. Overlap (`messe_overlap.py`, 160 Volltexte, `chunk_size = 200`)

| overlap | Chunks | relevante Sätze ganz (Review → lokal) | doppelte Wörter in Top-m | Top-m-Chunks mit Nachbar in Top-m |
|---|---|---|---|---|
| 0 | 5.755 | 83,0 → 83,5 % | 0,0 % | 46,0 → 45,0 % |
| 10 | 6.043 | 88,3 → 88,7 % | 1,5 % | 50,5 → 48,2 % |
| 20 | 6.370 | 92,1 → 92,3 % | 2,8 % | 49,8 → 48,0 % |
| **40** | **7.135** | **95,4 → 95,5 %** | **6,7 %** | **55,0 → 55,8 %** |
| 60 | 8.124 | 97,2 → 97,1 % | 11,0 % | 61,5 → 61,5 % |
| 80 | 9.431 | 97,9 → 98,2 % | 15,9 % | 64,8 → 65,8 % |
| 100 | 11.271 | 98,8 → 98,8 % | 22,0 % | 73,5 → 73,0 % |

### 4. PDF-Extraktoren gegen die LaTeX-Quelle (`messe_extraktion.py`, 25 Paper)

Erstmals ausgeführt, deshalb ohne Vergleich zum Review. Mediane über die Paper:

| Extraktor | recall | precision | unbekannte Wörter | Suchbegriffe gefunden | s/Paper |
|---|---|---|---|---|---|
| `pypdf` 6.21.1 | 95,3 % | 85,3 % | 4,9 % | 100 % | 0,20 |
| `pymupdf4llm` 0.3.4 | 96,4 % | 84,4 % | 5,3 % | 100 % | 1,44 |

Zwei Paper fehlen, weil arXiv trotz 3,1 s Pause mit HTTP 429 abgelehnt hat.

## Schlüsse

- Beide Probleme aus dem Review sind bestätigt: Auf Abstracts filtert die BM25-Vorauswahl nur Chunks ganz ohne Schlagwort, und die IDF des Hauptbegriffs liegt nahe null. Festgehalten als Einschränkung in ADR 0004.
- Volltext löst Problem 1 und entschärft Problem 2, braucht aber den Datenbank-Cache (ohne ihn etwa 3,5 Minuten pro Aufruf).
- `overlap = 40` bleibt: Es liegt am Knick zwischen ganzen Sätzen und doppelten Wörtern.
- Für Volltext reicht `pypdf`: praktisch gleich gut wie `pymupdf4llm`, siebenmal schneller, BSD- statt AGPL-Lizenz.
- arXiv drosselt mit HTTP 429 auch bei 3,1 s Abstand. Ein Volltext-Abruf im Tool braucht Wiederholen mit wachsender Wartezeit, nicht nur eine feste Pause.
