# AlgorithmusProjekt – News-Digest-Algorithmus

Ein Studienprojekt, das einen Algorithmus zur automatisierten Erstellung eines Nachrichten-Digests entwirft und dokumentiert. Der Algorithmus sammelt Artikel aus verschiedenen Quellen, dedupliziert sie thematisch, bewertet sie anhand gewichteter Kriterien, fasst sie per LLM zusammen und versendet den Digest per E-Mail.

Die algorithmische Spezifikation ist als Pseudocode formuliert und in [`Phase2/pseudocode.md`](Phase2/pseudocode.md) zu finden.

---

## Funktionsweise

Der Algorithmus durchläuft fünf Phasen:

1. **Sammeln** – Artikel werden von konfigurierten Quellen (RSS-/API-Endpunkte) abgerufen. Bei Fehlern kommt ein exponentielles Backoff mit bis zu `maxRetries` Versuchen zum Einsatz.
2. **Deduplizierung / Clustering** – Ähnliche Artikel werden anhand der Jaccard-Ähnlichkeit der Titel zu Themen-Clustern zusammengefasst (Schwelle `tau`).
3. **Ranking** – Jeder Cluster bekommt einen Score aus Aktualität, Keyword-Treffern und Quellenanzahl. Ein Min-Heap der Größe `N` hält die Top-Artikel.
4. **Zusammenfassung (LLM)** – Die Top-Artikel werden per LLM zu einem Digest zusammengefasst, mit Retry und Fallback (nur Titel + Link).
5. **Versand** – Der fertige Digest wird per SMTP versendet, mit Retry und Backoff bei Fehlern.

---

## Projektstruktur

```
AlgorithmusProjekt/
├── Phase2/
│   └── pseudocode.md   # Algorithmus-Spezifikation (Pseudocode)
├── Diagram.md         # (Platzhalter für Diagramme)
├── README.md          # Diese Datei
└── LICENSE            # MIT-Lizenz
```

---

## Eingaben und Parameter

| Parameter | Bedeutung | Beispiel |
|---|---|---|
| `S` | Liste der Quellen (RSS-/API-Endpunkte) | – |
| `K` | Interessen des Nutzers (Keywords) | – |
| `N` | Anzahl Artikel im Digest | 5 |
| `T` | Zeitfenster | 24 h |
| `tau` | Ähnlichkeitsschwelle für Clustering | 0.5 |
| `maxRetries` | Maximale Versuche pro Quelle | 3 |
| `w1, w2, w3` | Gewichte (Aktualität / Keyword / Quellen) | 0.4 / 0.4 / 0.2 |

---

## Entscheidungsregeln

| Regel | Bedingung | Folge |
|---|---|---|
| R1 | HTTP 200 und parsebar | Artikel übernehmen |
| R2 | Fetch fehlgeschlagen und `r < maxRetries` | Backoff, erneut versuchen |
| R3 | Fetch endgültig fehlgeschlagen | Quelle loggen, weiter mit nächster |
| R4 | `A` leer | Alarm, Abbruch |
| R5 | Jaccard `>= tau` | in bestehenden Cluster |
| R6 | Jaccard `< tau` | neuer Cluster |
| R7 | Heap-Größe `> N` | kleinsten Score entfernen |
| R8 | LLM-Antwort ungültig und `q < 2` | Retry |
| R9 | LLM endgültig ungültig | Fallback ohne Zusammenfassung |
| R10 | SMTP fehlgeschlagen und `k < 3` | Backoff, erneut senden |

---

## Komplexität

- **Fetch:** `O(|S|)`
- **Clustering:** `O(|A| · |Cluster|)`, im Worst Case `O(|A|²)`
- **Ranking mit Heap:** `O(|Cluster| · log N)`

---

## Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).
