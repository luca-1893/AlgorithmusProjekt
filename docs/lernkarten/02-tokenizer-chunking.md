# 02 Tokenizer und Chunking mit Überlappung

**In einem Satz:** Der Tokenizer macht aus Text eine Liste normalisierter Wörter für BM25, das Chunking zerlegt jedes Dokument in Abschnitte fester Wortzahl, die sich überlappen.

## Kernidee

- **Tokenizer:** kleinschreiben (`casefold`, aus „ß“ wird „ss“), Verbinder (Bindestrich, Apostroph) ersatzlos entfernen, jedes andere Nicht-Buchstaben/Ziffer-Zeichen durch Leerzeichen ersetzen, an Leerraum trennen. Keine Deduplizierung.
- Gedankenstriche (– —) sind keine Verbinder, sie trennen: „10–20“ → `10`, `20`.
- **Chunking:** feste Fenster von `chunk_size` Wörtern; benachbarte Chunks teilen `overlap` Wörter. Schrittweite = `chunk_size − overlap`.
- **Warum Überlappung:** Ein Satz mit höchstens `overlap + 1` Wörtern liegt immer ganz in einem Chunk; Sätze an der Grenze werden seltener zerrissen.
- Ein Chunk ist unveränderlich: `Chunk(document_id, position, text)`, Position ab 0. Metadaten bleiben am Dokument.
- Text eines Dokuments = Titel + Leerzeile + Abstract.

## Ablauf

```
WENN chunk_size <= 0 ODER overlap < 0 ODER overlap >= chunk_size: Fehler
schritt = chunk_size − overlap;  start = 0
SOLANGE start < Anzahl Wörter:
    Chunk = wörter[start .. start + chunk_size − 1]
    WENN start + chunk_size >= Anzahl Wörter: ABBRUCH   // Textende erreicht
    start = start + schritt
```

Anzahl Chunks bei n > chunk_size Wörtern: aufrunden((n − overlap) / schritt).

## Mini-Beispiel

- Tokenizer (Testdoku N1, R2): `"DEr  Apfel-Baum ist grün."` → `["der", "apfelbaum", "ist", "grün"]`; `"COVID-19 E-Mail don’t Straße"` → `["covid19", "email", "dont", "strasse"]`; `"and/or"` → `["and", "or"]`.
- Chunking (N2): `"w1 … w10"`, `chunk_size=4`, `overlap=1` → `["w1 w2 w3 w4", "w4 w5 w6 w7", "w7 w8 w9 w10"]`.
- Projektwerte (E6): 6.000 Wörter Volltext → (6.000 − 40) / 160 = 37,25 → **38 Chunks** mit zusammen 7.600 Wörtern, also rund 25 % mehr als der Volltext.

## Komplexität

Tokenizer O(C), C = Zeichen. Chunking O(n), n = Wörter; jedes Wort landet bei `overlap < chunk_size / 2` in höchstens zwei Chunks.

## Im Projekt

- `src/bm25/bm25.py` → `tokenize()`; `src/chunking/chunking.py` → `split_into_chunks()`, `create_chunks()`.
- `chunk_size=200`, `overlap=40` (`PipelineConfig`). Die meisten Abstracts passen in **einen** Chunk (20 Abstracts → 22–29 Chunks).
- `overlap=40` ist gemessen (160 Volltexte): relevante Sätze ganz in einem Chunk bei 0 → 83 %, 20 → 92 %, 40 → 95 %, 60 → 97 %; doppelte Wörter 40 → 7 %, 60 → 11 %, 100 → 22 %. 40 liegt am Knick.
- Die Datenbank prüft dieselbe Regel nochmal: `CHECK (overlap >= 0 AND overlap < chunk_size)` (E11).

## Typische Prüferfragen

- **Warum muss overlap < chunk_size sein?** Sonst ist die Schrittweite ≤ 0 und die Schleife kommt nie voran (Endlosschleife, Test F1).
- **Warum Wörter statt LLM-Tokens?** Kein Tokenizer des Sprachmodells nötig, für jedes Modell gleich (A3); Nachteil: Tokens pro Chunk schwanken.
- **Warum ist 40 der richtige Overlap?** Gemessen: Ab 40 steigt vor allem die Redundanz, kaum noch der Anteil ganzer Sätze.
- **Warum bricht die Schleife am Textende ab?** Ein weiterer Chunk bestünde nur aus Überlappung.

## Stolperfallen

- Chunking trennt an Leerraum (`text.split()`), BM25 zählt Tokens nach dem Tokenizer; die Längen können sich unterscheiden.
- Absätze gehen verloren, Chunks beginnen und enden mitten im Satz (L8).
