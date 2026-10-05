#  Pseudocode: News-Digest-Algorithmus

## Eingaben und Parameter

- S: Liste der Quellen (RSS-/API-Endpunkte)
- K: Interessen des Nutzers (Keywords)
- N: Anzahl Artikel im Digest (z. B. 5)
- T: Zeitfenster (z. B. 24 h)
- tau: Ähnlichkeitsschwelle (z. B. 0.5)
- maxRetries: 3
- w1, w2, w3: Gewichte (z. B. 0.4 / 0.4 / 0.2)

## Startbedingung

Trigger ausgelöst (Zeitplan 07:00 oder manueller Start), S nicht leer, SMTP- und LLM-Zugang konfiguriert.

## Endbedingungen

- Erfolg: Digest per SMTP versendet
- Abbruch 1: keine Artikel verfügbar (Admin-Alarm)
- Abbruch 2: SMTP dauerhaft fehlgeschlagen (Fehler geloggt)

## Algorithmus

```
ALGORITHMUS NewsDigest(S, K, N, T, tau)

  A <- leere Liste                      // alle Artikel
  Cluster <- leere Liste                // Themen-Cluster

  // Phase 1: Sammeln
  FÜR JEDE Quelle s IN S:
      r <- 0
      ERFOLG <- FALSCH
      SOLANGE r <= maxRetries UND NICHT ERFOLG:
          antwort <- fetch(s)
          WENN antwort.status = 200 UND parsebar(antwort):
              FÜR JEDEN Artikel a IN parse(antwort):
                  WENN alter(a) <= T:
                      A.anhängen(a)
              ERFOLG <- WAHR
          SONST:
              WENN r < maxRetries:
                  warte(2^r Sekunden)   // exponentielles Backoff
              r <- r + 1
      WENN NICHT ERFOLG:
          log("Quelle ausgefallen: " + s)

  // Sonderfall: nichts gesammelt
  WENN A ist leer:
      alarm_admin("Keine Artikel verfügbar")
      ENDE (Abbruch)

  // Phase 2: Deduplizierung (Clustering)
  FÜR JEDEN Artikel a IN A:
      bestes_c <- NULL
      beste_sim <- 0
      FÜR JEDEN Cluster c IN Cluster:
          sim <- jaccard(tokens(a.titel), tokens(c.repräsentant.titel))
          WENN sim > beste_sim:
              beste_sim <- sim
              bestes_c <- c
      WENN beste_sim >= tau:
          bestes_c.artikel.anhängen(a)
      SONST:
          Cluster.anhängen(neuer Cluster mit a)

  // Phase 3: Ranking (Min-Heap der Größe N)
  H <- leerer Min-Heap
  FÜR JEDEN Cluster c IN Cluster:
      c.score <- w1 * aktualität(c) + w2 * keywordTreffer(c, K) + w3 * anzahlQuellen(c)
      H.push(c)
      WENN größe(H) > N:
          H.pop()                       // kleinster Score fliegt raus
  TopN <- H nach Score absteigend sortiert

  // Phase 4: Zusammenfassung per LLM
  q <- 0
  zusammenfassung <- NULL
  SOLANGE q <= 2 UND zusammenfassung = NULL:
      text <- llm(baue_prompt(TopN))
      WENN gültig(text):                // nicht leer, Länge im Rahmen
          zusammenfassung <- text
      SONST:
          q <- q + 1
  WENN zusammenfassung = NULL:
      zusammenfassung <- fallback(TopN) // nur Titel + Link

  // Phase 5: Versand
  body <- render(zusammenfassung)
  k <- 0
  SOLANGE k < 3:
      WENN smtp_send(body):
          ENDE (Erfolg)
      warte(2^k Sekunden)
      k <- k + 1
  log("SMTP fehlgeschlagen")
  ENDE (Fehler)
```

## Entscheidungsregeln im Überblick

| Regel | Bedingung | Folge |
|---|---|---|
| R1 | HTTP 200 und parsebar | Artikel übernehmen |
| R2 | Fetch fehlgeschlagen und r < maxRetries | Backoff, erneut versuchen |
| R3 | Fetch endgültig fehlgeschlagen | Quelle loggen, weiter mit nächster |
| R4 | A leer | Alarm, Abbruch |
| R5 | Jaccard >= tau | in bestehenden Cluster |
| R6 | Jaccard < tau | neuer Cluster |
| R7 | Heap-Größe > N | kleinsten Score entfernen |
| R8 | LLM-Antwort ungültig und q < 2 | Retry |
| R9 | LLM endgültig ungültig | Fallback ohne Zusammenfassung |
| R10 | SMTP fehlgeschlagen und k < 3 | Backoff, erneut senden |

## Komplexität

- Fetch: O(|S|)
- Clustering: O(|A| · |Cluster|), im Worst Case O(|A|²)
- Ranking mit Heap: O(|Cluster| · log N)