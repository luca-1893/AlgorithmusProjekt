# 11 MCP und FastMCP

**In einem Satz:** Das Model Context Protocol (MCP) ist ein offener Standard, über den Sprachmodell-Clients externe Tools aufrufen; FastMCP macht aus einer Python-Funktion ein solches Tool, hier `research_papers`.

## Kernidee

- **MCP:** Client (z. B. Claude Desktop, Claude Code) und Server sprechen ein festes Protokoll; der Server meldet seine Tools mit Name, Beschreibung und Parametern, das Modell entscheidet, wann es sie aufruft.
- **FastMCP:** Python-Bibliothek; ein Dekorator `@server.tool` macht aus Typ-Hinweisen und Beschreibungen das Tool-Schema.
- **Ein Tool:** `research_papers`, nur lesend und mit Zugriff auf externe Quellen (`readOnlyHint`, `openWorldHint`).
- **Fehler:** `ToolError` landet als Meldung beim Modell, der Server läuft weiter.
- **Transport:** stdio (Client startet den Server als Prozess, lokal) oder HTTP (Webdienst, Endpunkt `/mcp`).

## Ablauf

```
research_papers(keywords, k = 5, question = "", published_after = "", peer_reviewed_only = false)
    WENN k nicht 1..20: ToolError
    filter = SearchFilter(published_from = Datum(published_after), peer_reviewed_only)
    ergebnis = research(keywords, k, source, embedder, question, config, filter)
    ValueError → ToolError(Meldung);  SourceError → ToolError("research source not reachable: …")
    GIB {hits: [...], warnings: [...]} ZURÜCK
```

## Mini-Beispiel

Starten lokal: `PYTHONPATH=src .venv/bin/python -m mcp_server`; als Webdienst: `... -m mcp_server --transport http --host 0.0.0.0 --port 8000`. Felder je Treffer (`Hit.to_dict`): `document_id`, `title`, `authors`, `published`, `url`, `source`, `categories`, `peer_reviewed`, `journal_ref`, `doi`, `chunk_position`, `text`, `score`. Beispiel für `warnings`: „Dokumente aus dem Cache“, „Cache nicht verfügbar“.

## Im Projekt

- `src/mcp_server/mcp_server.py`: `build_server`, `research_papers`, `parse_date`, `main`; `MAX_K = 20`.
- Standard-Quelle: `CachedSource(ArxivSource())`; Standard-Einbetter: `CachedEmbedder(VoyageEmbedder())`, wenn `VOYAGE_API_KEY` gesetzt, sonst keiner (nur BM25).
- Parameterbeschreibung verlangt „2 to 8 English technical terms“ (wegen L4).
- In `.mcp.json` für Claude Code eingetragen; Anleitung für Claude Desktop: `docs/mcp_server/einrichtung.md`.
- Tool-Vertrag ist mit `src/evaluation/messlauf.py` geteilt: Parameter und JSON-Felder nur gemeinsam ändern.

## Typische Prüferfragen

- **Warum stdio und HTTP?** stdio für lokale Clients ohne Netzwerk; HTTP, damit das Tool auf einem eigenen Server laufen kann (ADR 0001).
- **Wie ist der HTTP-Dienst abgesichert?** Noch gar nicht, keine Anmeldung; nur hinter VPN oder Reverse-Proxy mit Token betreiben (L10).
- **Warum ist k auf 20 begrenzt?** Riesige Antworten würden die Token-Ersparnis zunichtemachen (R1).
- **Was sieht das Modell bei einem arXiv-Ausfall?** Eine Fehlermeldung „research source not reachable: …“; der Server stürzt nicht ab.

## Stolperfallen

- Der Client braucht absolute Pfade zur `.venv`-Python und `PYTHONPATH` auf `src`, sonst `ModuleNotFoundError`.
- Kategorien und ein Enddatum kennt `SearchFilter`, das Tool bietet sie aber nicht als Parameter an.
