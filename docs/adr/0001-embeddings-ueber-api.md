# ADR 0001: Embeddings über eine API statt lokal

- **Status:** angenommen (Anbieter noch offen)
- **Datum:** 2026-10-15
- **Entschieden von:** Luca

## Kontext

Die Vektorsuche braucht für die Anfrage und für jeden Kandidaten-Chunk einen Vektor (Embedding). Den erzeugt ein Embedding-Modell. Das Tool soll als MCP-Server auf einem eigenen Server laufen und nicht nur lokal auf einem Entwicklerrechner.

## Entscheidung

Die Embeddings kommen von einem externen Anbieter über dessen API. Der API-Schlüssel wird über eine Umgebungsvariable gesetzt und nicht im Repo gespeichert.

## Betrachtete Alternativen

| Alternative | Vorteil | Nachteil |
|---|---|---|
| Lokales Modell (z. B. `sentence-transformers`) | Keine laufenden Kosten, kein Schlüssel, keine Netzwerkabhängigkeit | Schwere Abhängigkeit (Modell und Laufzeitbibliothek), braucht Rechenleistung und Speicher auf dem Server |
| **Externe API** | Leichte Abhängigkeit, keine Rechenlast auf dem Server, aktuelle Modelle | Kosten pro Aufruf, Schlüssel nötig, abhängig von Erreichbarkeit und Limits des Anbieters |

## Konsequenzen

- Jede Anfrage verursacht API-Aufrufe für die Anfrage und die m Kandidaten. Die Keyword-Vorauswahl per BM25 hält m klein und damit auch die Kosten.
- Fällt die API aus oder ist der Schlüssel ungültig, braucht der Ablauf einen eigenen Fehlerpfad. Er fehlt im Flowchart noch.
- Wer das Notebook ausführt, braucht einen eigenen Schlüssel. Das ist eine Abweichung von der Hackathon-Vorgabe „lauffähig ohne Anpassung“ und gehört in die Reflexion.
- Der Anbieter bestimmt die Vektorlänge. Vektoren verschiedener Modelle sind nicht vergleichbar, ein späterer Wechsel des Anbieters erfordert neues Einbetten.

## Offen

- Welcher Anbieter (Kandidaten: Voyage AI, OpenAI, Cohere, Mistral)
- Kostenrahmen pro Anfrage, sobald der Anbieter feststeht
