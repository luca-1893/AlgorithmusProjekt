# ADR 0002: PostgreSQL als Datenbank

- **Status:** angenommen (Umgang mit Vektoren noch offen)
- **Datum:** 2026-10-15
- **Entschieden von:** Luca

## Kontext

Ohne Datenbank hält das Tool alles nur für die Dauer eines Aufrufs im Speicher. Dadurch werden dieselben Quellen bei jedem Aufruf neu geholt und eingebettet, dasselbe Paper aus zwei Quellen ist nicht als Duplikat erkennbar, und für die KPI-Auswertung fehlt ein Ort für die Messläufe. Das Tool läuft auf einem eigenen Server. Die SQL-Queries schreibt und optimiert Luca selbst, mit DataGrip.

## Entscheidung

Dokumente, Chunks und Messläufe werden in PostgreSQL auf dem Server gespeichert.

## Betrachtete Alternativen

| Alternative | Vorteil | Nachteil |
|---|---|---|
| Keine Datenbank | Kein Betriebsaufwand | Kein Cache, keine Duplikaterkennung, Messläufe gehen verloren |
| SQLite | Eine Datei, keine Installation | Schwach bei mehreren gleichzeitigen Zugriffen, praxisfern für einen Server |
| **PostgreSQL** | Läuft auf dem Server, DataGrip verbindet sich direkt, praxisnah, Erweiterungen wie `pgvector` verfügbar | Muss installiert, abgesichert und gesichert werden |

## Konsequenzen

- Der Server braucht eine PostgreSQL-Instanz mit eigenem Benutzer für das Tool; Zugangsdaten kommen über Umgebungsvariablen, nicht ins Repo.
- Tests, die die Datenbank berühren, brauchen eine eigene Test-Datenbank, damit sie keine echten Daten verändern.
- Die SQL-Statements liegen als eigene Dateien im Repo; der Python-Code führt sie nur aus.

## Offen

- Werden die Vektoren mit `pgvector` gespeichert, und übernimmt die Datenbank auch die Ähnlichkeitssuche? Vorschlag: Vektoren speichern, die Cosine Similarity selbst rechnen und `pgvector` in Phase 5 als Vergleich messen.

## Nachtrag 2026-10-16: lokale Einrichtung

- PostgreSQL 18.6 per Homebrew (`postgresql@18`), läuft als Dienst; Datenbanken `algorithmusprojekt` und `algorithmusprojekt_test`.
- Python-Treiber `psycopg` 3.3.6 (mit Binärpaket, läuft auf Python 3.15).
- Verbindung über `DATABASE_URL`, Standard `postgresql:///algorithmusprojekt`; Tests nutzen `TEST_DATABASE_URL`, Standard die Test-Datenbank.
- SQL liegt als Dateien in `sql/` und wird von Luca geschrieben; die Anforderungen stehen in `docs/storage/sql-aufgaben.md`.

