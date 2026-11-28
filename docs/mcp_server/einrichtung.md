# Einrichtung des MCP-Tools für neue Nutzer

Ziel: Das Tool `research_papers` läuft auf einem neuen Rechner und lässt sich aus Claude Desktop (oder Claude Code) aufrufen. Dauer etwa 20–30 Minuten. Geschrieben für die Übungssession am 30.11.2026.

Was **nicht** nötig ist:

- **Voyage-Key:** Ohne `VOYAGE_API_KEY` arbeitet das Tool nur mit BM25 (Regel R6). Für einen ersten Test reicht das.
- **PostgreSQL:** Ohne Datenbank läuft das Tool ohne Cache weiter und meldet „Cache nicht verfügbar“ in `warnings` (R15).
- **Anthropic-API-Key:** Nur für die Messläufe (`evaluation.messlauf`), nicht für das Tool.

Gut zu wissen: Das Tool lädt seit dem 28.11.2026 den Volltext der Paper (HTML-Fassung, sonst PDF; ADR 0006). Der erste Aufruf zu einer Frage dauert deshalb deutlich länger (Rauchtest mit 5 Dokumenten: 16 s; bei 20 Dokumenten geschätzt über eine Minute), eine wiederholte Suche kommt aus dem Cache. Wer nur Titel und Abstract will, startet den Server mit `--abstract-only`.

## 1. Voraussetzungen

| | macOS | Windows |
|---|---|---|
| Python 3.15 | `brew install python@3.15` | Installer von python.org, Haken bei „Add python.exe to PATH“ und „py launcher“ |
| Git | `xcode-select --install` | git-scm.com |
| Claude Desktop | claude.ai/download | claude.ai/download |

Prüfen: `python3.15 --version` (macOS) bzw. `py -3.15 --version` (Windows) zeigt `Python 3.15.x`. Ältere Versionen gehen nicht; macOS bringt ein Python 3.9 mit, das hier **nicht** funktioniert.

## 2. Projekt holen und einrichten

macOS:

```
git clone https://github.com/luca-1893/AlgorithmusProjekt.git
cd AlgorithmusProjekt
python3.15 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Windows (PowerShell):

```
git clone https://github.com/luca-1893/AlgorithmusProjekt.git
cd AlgorithmusProjekt
py -3.15 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## 3. Prüfen, ob alles läuft

Tests (aus dem Projektordner; ohne Datenbank werden die Storage-, Cache- und Teile der Evaluation-Tests übersprungen, das ist hier in Ordnung):

```
.venv/bin/python -m unittest discover -s src -t src          # macOS
.venv\Scripts\python -m unittest discover -s src -t src      # Windows
```

Erwartet: am Ende `OK` (ggf. mit `skipped=…`).

Server von Hand starten (macOS; Windows analog mit `.venv\Scripts\python` und `$env:PYTHONPATH="src"`):

```
PYTHONPATH=src .venv/bin/python -m mcp_server
```

Der Server wartet dann still auf Eingaben über stdio; das ist richtig. Mit Strg+C beenden.

## 4. In Claude Desktop eintragen

Claude Desktop → Einstellungen → Entwickler → „Konfiguration bearbeiten“ öffnet `claude_desktop_config.json`:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Eintrag (Pfade an den eigenen Projektordner anpassen, **absolute** Pfade verwenden):

macOS:

```json
{
  "mcpServers": {
    "recherche": {
      "command": "/Users/<name>/AlgorithmusProjekt/.venv/bin/python",
      "args": ["-m", "mcp_server"],
      "env": {
        "PYTHONPATH": "/Users/<name>/AlgorithmusProjekt/src"
      }
    }
  }
}
```

Windows (Backslashes in JSON doppelt schreiben):

```json
{
  "mcpServers": {
    "recherche": {
      "command": "C:\\Users\\<name>\\AlgorithmusProjekt\\.venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_server"],
      "env": {
        "PYTHONPATH": "C:\\Users\\<name>\\AlgorithmusProjekt\\src"
      }
    }
  }
}
```

Steht in der Datei schon etwas, nur den Block `"recherche": {…}` innerhalb von `"mcpServers"` ergänzen.

Danach Claude Desktop **ganz beenden** (macOS: ⌘Q, Windows: im Infobereich „Beenden“) und neu starten. Im Chat erscheint unter dem Werkzeug-Symbol der Server `recherche` mit einem Tool.

## 5. Testfrage

> A method copies the terms that a cross-encoder treats as decisive in semantic search results into the BM25 query. How much does it raise Recall@100 on Natural Questions?

Erwartet: Claude ruft `research_papers` auf (beim ersten Mal nach Erlaubnis fragen lassen) und zitiert arXiv **2608.00452**, Antwort „von 0,32 auf 0,47“ (Frage F21 aus `docs/evaluation/testfragen.md`). Ohne Voyage-Key steht kein Hinweis zur Vektorsuche in `warnings`; ohne Datenbank steht dort „Cache nicht verfügbar“.

## 6. Optional: Vektorsuche mit Voyage

Eigenen Key bei voyageai.com anlegen (kostenloses Kontingent reicht für Tests); Keys nicht weitergeben. In der Konfiguration unter `"env"` ergänzen:

```json
"VOYAGE_API_KEY": "<eigener-key>"
```

Die Datei liegt nur lokal; sie nicht ins Repo kopieren. Danach Claude Desktop neu starten.

## 7. Optional: Datenbank für den Cache

Nur macOS beschrieben (siehe README, Abschnitt „Datenbank“):

```
brew install postgresql@18
brew services start postgresql@18
/opt/homebrew/opt/postgresql@18/bin/createdb algorithmusprojekt
/opt/homebrew/opt/postgresql@18/bin/psql -d algorithmusprojekt -f sql/schema.sql
```

Danach liefert eine wiederholte Frage „Dokumente aus dem Cache“ in `warnings`.

## Wenn es nicht klappt

| Zeichen | Ursache | Lösung |
|---|---|---|
| `recherche` erscheint nicht in Claude Desktop | Desktop nicht ganz beendet, oder JSON fehlerhaft | ⌘Q bzw. Beenden im Infobereich; JSON z. B. auf jsonlint.com prüfen |
| Server „failed“ in den Einstellungen | falscher Pfad zu `python` oder `src` | Log ansehen: macOS `~/Library/Logs/Claude/mcp-server-recherche.log`, Windows `%APPDATA%\Claude\logs\` |
| `ModuleNotFoundError: fastmcp` | falsches Python (z. B. System-Python 3.9) | `command` muss auf `.venv/…/python` zeigen; Schritt 2 wiederholen |
| `ModuleNotFoundError: mcp_server` | `PYTHONPATH` fehlt oder zeigt nicht auf `src` | absoluten Pfad zu `src` eintragen |
| Tool antwortet „research source not reachable“ | keine Verbindung zu arXiv | Netzwerk/VPN prüfen; arXiv drosselt bei vielen Anfragen kurz hintereinander |
| In PyCharm läuft nichts | PyCharm nutzt ein anderes Python | Settings → Python Interpreter → `.venv` auswählen |
