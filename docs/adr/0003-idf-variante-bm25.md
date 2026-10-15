# ADR 0003: IDF-Variante mit +1 für BM25

- **Status:** angenommen
- **Datum:** 2026-10-15
- **Entschieden von:** Luca

## Kontext

BM25 gewichtet jedes Anfragewort mit seiner Inverse Document Frequency (IDF): Seltene Wörter zählen mehr als häufige. Für die IDF gibt es mehrere Formeln. Die klassische Variante nach Robertson wird negativ, sobald ein Wort in mehr als der Hälfte der Dokumente vorkommt. Ein negatives Gewicht bedeutet, dass ein Dokument schlechter bewertet wird, **weil** es ein Anfragewort enthält. Bei kleinen Korpora, wie sie nach der Recherche-Vorauswahl entstehen, passiert das schnell.

Werte bei N = 3 Dokumenten (df = Anzahl Dokumente, die das Wort enthalten):

| df | klassisch `ln((N − df + 0.5) / (df + 0.5))` | mit +1 `ln((N − df + 0.5) / (df + 0.5) + 1)` |
|---|---|---|
| 0 | 1.946 | 2.079 |
| 1 | 0.511 | 0.981 |
| 2 | −0.511 | 0.470 |
| 3 | −1.946 | 0.134 |

## Entscheidung

Die IDF wird mit der +1-Variante berechnet:

`IDF(q) = ln( (N − df + 0.5) / (df + 0.5) + 1 )`

## Betrachtete Alternativen

| Alternative | Vorteil | Nachteil |
|---|---|---|
| Klassisch (Robertson) | Originalformel aus der Literatur | Negativ ab df > N/2, bestraft Treffer |
| Klassisch, negative Werte auf 0 bzw. ε setzen | Nie negativ | Nachträglicher Workaround mit Sonderfall; alle häufigen Wörter bekommen dasselbe Gewicht |
| **Mit +1 (Lucene/Elasticsearch)** | Argument von `ln` ist immer > 1, IDF daher immer > 0, ohne Sonderfall; Reihenfolge seltener vor häufig bleibt erhalten | Weicht von der Originalformel ab; sehr häufige Wörter behalten ein kleines positives Gewicht |

## Konsequenzen

- `berechne_idf(df, N)` bekommt nur Zahlen und braucht keine Fallunterscheidung.
- Ein unbekanntes Wort (df = 0) bekommt eine hohe IDF, trägt aber nichts zum Score bei, weil seine Termhäufigkeit in jedem Dokument 0 ist.
- Ein Test prüft, dass die IDF auch bei df = N noch > 0 ist.
- N = 0 (leerer Index) fängt der Aufrufer vor der IDF-Berechnung ab.
