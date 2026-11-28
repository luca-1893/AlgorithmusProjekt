# ADR 0006: Volltext aus der HTML-Fassung, sonst PDF, sonst Abstract

- **Status:** angenommen
- **Datum:** 2026-11-28
- **Entschieden von:** Luca (umgesetzt von Claude im Auftrag)

## Kontext

ADR 0004 hat festgehalten, dass die BM25-Vorauswahl auf Titel und Abstract kaum filtert (L1), die IDF des Hauptschlagworts gegen null geht (L2) und Antworten, die nur im Volltext stehen, gar nicht gefunden werden (L3). Die Messung dazu (`messungen/2026-10-19_review-pr24/`, 8 Anfragen, je 20 Dokumente):

| | Abstract | Volltext |
|---|---|---|
| Chunks pro Anfrage | 22–29 | 515–1.167 |
| von der Vorauswahl aussortiert | ≈ 10 % | 90–96 % |
| IDF des Hauptbegriffs, z. B. `uml` | 0,10 | 0,62 |

Der Volltext wurde damals zurückgestellt, weil er ohne Cache etwa 3,5 Minuten pro Tool-Aufruf kostet. Seit dem 15.11.2026 gibt es den Datenbank-Cache (R13–R16), und das Schema ist für Volltext vorbereitet: `documents.origin` in `html`, `pdf`, `abstract`, `full_text` ist genau bei `abstract` leer (`documents_invalid_full_text`). Luca hat entschieden, den Volltext jetzt umzusetzen.

## Optionen

**Woher der Text kommt**

| Option | Vorteil | Nachteil |
|---|---|---|
| **HTML-Fassung** (`export.arxiv.org/html/<id>`, von arXiv mit LaTeXML erzeugt) | Struktur ist erhalten: Abschnitte, Literaturverzeichnis, Formeln, Tabellen sind als Elemente markiert und lassen sich gezielt weglassen; keine Bibliothek nötig (`html.parser` aus der Standardbibliothek) | gibt es nicht für jedes Paper (vor allem ältere ohne LaTeX-Quelle), manchmal nur eine Fehlerseite |
| **PDF mit `pypdf`** | gibt es für jedes Paper | Kopf- und Fußzeilen, zerrissene Wörter, Formelreste; Literaturverzeichnis nur über die Überschrift erkennbar |
| PDF mit `pymupdf4llm` | etwas höherer Recall (96,4 % gegen 95,3 %) | siebenmal langsamer (1,44 s gegen 0,20 s pro Paper), AGPL-Lizenz |
| LaTeX-Quelle | genaueste Referenz | braucht `pandoc`, viele Sonderfälle (`\input`, eigene Makros); in der Messung nur als Referenz genutzt |

Vergleich der PDF-Extraktoren: `messungen/2026-10-19_review-pr24/README.md`, Abschnitt 4 (25 Paper, Mediane).

**Wie mit der Drosselung umgehen** (arXiv antwortet auch bei 3,1 s Abstand mit HTTP 429)

| Option | Warum (nicht) |
|---|---|
| feste Pause allein | reicht laut Messung nicht |
| **Pause plus Wiederholen mit wachsender Wartezeit, begrenzt** | übersteht kurze Drosselung; die Grenze verhindert, dass ein Tool-Aufruf minutenlang hängt |
| parallele Downloads | schneller, verstößt aber gegen die Nutzungsregeln von arXiv und verschärft die Drosselung |

**Was passiert, wenn kein Volltext kommt**

| Option | Warum (nicht) |
|---|---|
| Dokument weglassen | verliert ein Paper, das arXiv als relevant geliefert hat |
| Fehler an das Sprachmodell | widerspricht Fail-open (AGENTS.md, Regel 3) |
| **Abstract verwenden, Hinweis in `warnings`** | die Recherche gelingt immer, das Sprachmodell sieht, für welche Paper nur das Abstract vorlag |

## Entscheidung

- **HTML vor PDF vor Abstract** (R17, `src/sources/fulltext.py`). Aus der HTML-Seite zählt nur `<article>`, ohne Formeln, Tabellen, Abbildungen, Navigation, Autorenblock, Fußnoten und Literaturverzeichnis. Aus dem PDF wird der Text aller Seiten mit `pypdf` gelesen, das Literaturverzeichnis ab der letzten Überschrift „References“/„Bibliography“ in der zweiten Hälfte abgeschnitten und Trennstriche am Zeilenende entfernt. Unter 500 Wörtern gilt eine Extraktion als gescheitert.
- **Server `export.arxiv.org`** wie die arXiv-API und die Messskripte; arXiv empfiehlt diesen Server für Programme. Die Inhalte sind dieselben wie unter `arxiv.org` (am 28.11. geprüft: gleiche Seite, gleiche Größe).
- **Nacheinander, 3,1 s Abstand zwischen zwei Anfragen**, auch zwischen der Suchanfrage und dem ersten Download. HTTP 429 und 503 werden bis zu viermal versucht, mit 5, 10 und 20 s Wartezeit dazwischen. Bleibt arXiv danach bei 429, bekommen die übrigen Dokumente dieses Aufrufs nur das Abstract (Hinweis „arXiv drosselt …“); der nächste Aufruf versucht es wieder. Andere Fehler (404 = keine HTML-Fassung, Netzwerk, Zeitüberschreitung) werden nicht wiederholt.
- **Rückfall auf das Abstract** mit dem Hinweis „Volltext nicht verfügbar für n von m Dokumenten, dort nur Titel und Abstract: <ids>“.
- **Schalter an der Quelle**, nicht in der Pipeline: `ArxivSource(full_text=True)`. Die Pipeline chunkt weiter `document.text`; das ist jetzt Titel plus Volltext, wenn einer vorliegt. Der MCP-Server schaltet den Volltext standardmäßig ein (`--abstract-only` schaltet ihn aus). `evaluation.messlauf` bleibt ohne Option bei Abstract und ohne Cache; mit `--volltext` lädt das Tool Volltexte, ebenfalls ohne Cache.
- **Cache speichert `origin` und `full_text`** (C8) und gibt sie bei einer gespeicherten Suche zurück. Liegt in einer gespeicherten Suche ein Dokument nur als Abstract vor, lädt der Volltext-Modus genau dieses nach (C14). Der Abstract-Modus lässt gespeicherte Volltexte weg (C15). Am Schema ändert sich nichts.

## Konsequenzen

- **Latenz beim ersten Abruf:** Jedes neue Paper kostet eine Anfrage (HTML) oder zwei (PDF), mit 3,1 s Abstand. Gemessen am 28.11.2026 (Rauchtest, `["BM25", "information retrieval"]`, `max_documents = 5`, nur BM25, lokale Datenbank): erster Abruf 15,9 s, gleiche Anfrage aus dem Cache 0,1 s, Abstract ohne Cache 0,3 s; alle 5 Paper kamen als HTML, zusammen 278 Chunks (zum Vergleich ADR 0004: 22–29 Chunks bei 20 Abstracts). Bei 20 Dokumenten sind ohne Cache mindestens etwa 65 s zu erwarten (20 × 3,1 s plus Download und Extraktion), mit PDF-Rückfällen und 429 deutlich mehr. Gemessen ist das noch nicht.
- Ob ein MCP-Client so lange auf ein Tool wartet, hängt vom Client ab; ein Zeitlimit pro Aufruf gibt es im Tool noch nicht.
- Wiederverwendet wird ein Volltext nur über eine gespeicherte Suche. Taucht ein bekanntes Paper in einer anderen Suche auf, wird es neu geladen, weil es keine Abfrage „Dokument nach arXiv-ID“ gibt (`docs/cache/cache-pseudocode.md`, Bekannte Grenzen). Das bräuchte eine neue SQL-Datei, die Luca schreiben will.
- Mit Volltext entstehen pro Anfrage Hunderte Chunks; der Index wird bei jedem Aufruf neu gebaut (L10). Die Vorauswahl hält die Einbettung trotzdem bei höchstens m = 50 Chunks.
- L1 und L3 sind damit umgesetzt, L2 nur entschärft (die IDF hängt weiter am Treffersatz). Gemessen im Messlauf ist der Volltext noch nicht; das macht Leitfrage L6 mit `--volltext`. Die Läufe stehen in `runs` mit dem Präfix „[Volltext]“ vor der Frage, weil `runs.variant` nur `agent_websearch`, `bm25` und `hybrid` erlaubt.
- Beim Rauchtest gefunden und behoben: Die aktuelle LaTeXML-Fassung gibt `<article>` die Klasse `ltx_authors_1line`; ein Vergleich auf Teilstrings (wie im Messskript) übersprang dadurch das ganze Paper. `pypdf` liefert manchmal NUL-Zeichen, die PostgreSQL in `text` ablehnt; sie werden entfernt.
- Neue Abhängigkeit `pypdf` (BSD-Lizenz) in `requirements.txt`; sie wird erst beim ersten PDF geladen.
