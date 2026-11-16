# ADR 0001: Embeddings über eine API statt lokal

- **Status:** angenommen, Anbieter Voyage AI (Nachtrag 2026-10-16)
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

## Nachtrag 2026-10-16: Anbieter Voyage AI

Entschieden von Luca. Umgesetzt als `VoyageEmbedder` in `src/vector_search/`, Modell `voyage-4` (1024 Dimensionen), Schlüssel aus `VOYAGE_API_KEY`.

| Kandidat | Kostenlos | Danach | Bemerkung |
|---|---|---|---|
| **Voyage AI** | 200 Mio. Tokens | 0,02–0,12 $ pro Mio. Tokens | von Anthropic empfohlen, getrennte Einbettung für Anfrage und Dokument |
| Jina AI (`jina-embeddings-v3`) | 10 Mio. Tokens | ab etwa 0,02 $ pro Mio. | Sitz in Berlin, 89 Sprachen |
| OpenAI (`text-embedding-3-small`) | – | 0,02 $ pro Mio. | verbreitet |
| Cohere (`embed-v4`) | Test-Schlüssel | 0,10 $ pro Mio. | über 100 Sprachen |

Ausschlaggebend war das große Freikontingent. Die Dokumentation nennt die 200 Mio. Tokens ausdrücklich für die Modellreihe 3; ob `voyage-4` dasselbe Kontingent hat, ist im Voyage-Dashboard zu prüfen, sonst `voyage-3.5` als Modell setzen. Pro Anfrage werden die Anfrage und bis zu m = 50 Abstracts eingebettet, grob 10.000 Tokens; 200 Mio. Tokens reichen damit für etwa 20.000 Anfragen.

Konsequenzen:

- Anfrage und Chunks werden in zwei Aufrufen eingebettet (`input_type` „query“ und „document“), weil Voyage beide unterschiedlich darstellt.
- HTTP-, Netzwerk- und Formatfehler werden zu `EmbeddingError`; die Pipeline liefert dann nur BM25-Ergebnisse mit Hinweis. Der Fehlerpfad im Flowchart ist damit festgelegt.
- Die hohen Limits gelten erst mit hinterlegter Zahlungsmethode, das Freikontingent bleibt dabei erhalten. Ohne Zahlungsmethode sind die Limits deutlich niedriger.
- Es gibt kein automatisches Wiederholen bei HTTP 429.
