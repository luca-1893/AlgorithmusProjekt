FUNKTION baue_server(quelle, einbetter, konfiguration)
    EINGABE:  quelle        – Recherche-Quelle, Standard ArxivQuelle
              einbetter     – Einbetter oder LEER; Standard: Voyage, falls VOYAGE_API_KEY
                              gesetzt ist, sonst LEER (dann nur BM25)
              konfiguration – Pipeline-Konfiguration
    AUSGABE:  MCP-Server mit genau einem Tool: research_papers

    server ← neuer FastMCP-Server "AlgorithmusProjekt Recherche"
    registriere research_papers(schlagwörter, k, frage) als nur lesendes Tool,
        das auf externe Quellen zugreift
    GIB server ZURÜCK
ENDE
// Quelle und Einbetter werden übergeben, damit Tests ohne Netzwerk laufen


FUNKTION research_papers(schlagwörter, k, frage, veröffentlicht_ab, nur_begutachtet)
    EINGABE:  schlagwörter – 2 bis 8 englische Fachbegriffe vom Sprachmodell
              k            – Anzahl gewünschter Abschnitte, 1 bis MAX_K (20)
              frage        – ursprüngliche Frage in beliebiger Sprache, darf leer sein
              veröffentlicht_ab – "JJJJ" oder "JJJJ-MM-TT", leer = keine Grenze
              nur_begutachtet   – WAHR: nur Paper mit Zeitschriftenverweis oder DOI
    AUSGABE:  {hits: [...], warnings: [...]} als JSON

    WENN k < 1 ODER k > MAX_K:
        TOOL-FEHLER "k muss zwischen 1 und MAX_K liegen"
                                          // schützt vor riesigen Antworten,
                                          // die die Token-Ersparnis zunichtemachen
    VERSUCHE:
        suchfilter ← Suchfilter(ab = Datum aus veröffentlicht_ab, nur_begutachtet)
        ergebnis ← recherchiere(schlagwörter, k, quelle, einbetter, frage, konfiguration, suchfilter)
    BEI ungültiger Eingabe (auch unlesbares Datum): TOOL-FEHLER mit der Meldung
    BEI Quellenfehler:        TOOL-FEHLER "Recherche-Quelle nicht erreichbar: …"
    GIB ergebnis als Dict ZURÜCK
ENDE
// Ein Tool-Fehler landet als Fehlermeldung beim Sprachmodell, der Server läuft weiter
// Laufzeit: wie recherchiere


FUNKTION starte(transport, host, port)
    transport "stdio" (Standard): Client startet den Server als Prozess,
                                  z. B. Claude Code oder Claude Desktop lokal
    transport "http":             Server läuft als Webdienst unter host:port/mcp
    baue_server() und starte ihn mit dem gewählten Transport
ENDE
// Bekannte Grenzen: über HTTP noch ohne Anmeldung, deshalb nur hinter einem
// abgesicherten Zugang (z. B. VPN oder Reverse-Proxy mit Token) betreiben
