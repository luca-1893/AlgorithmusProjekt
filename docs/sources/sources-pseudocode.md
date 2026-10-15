FUNKTION normalisiere_schlagwörter(schlagwörter)
    EINGABE:  schlagwörter – Liste von Strings, wie sie das LLM liefert
    AUSGABE:  Liste ohne Leerraum am Rand, ohne leere Einträge und ohne
              Duplikate (Groß-/Kleinschreibung egal), Reihenfolge bleibt

    ergebnis ← leere Liste
    gesehen  ← leere Menge
    FÜR JEDES wort IN schlagwörter:
        bereinigt ← wort ohne Leerraum am Anfang und Ende,
                    innerer Leerraum auf ein Leerzeichen reduziert
        schlüssel ← bereinigt in Kleinbuchstaben (casefold)
        WENN bereinigt nicht leer UND schlüssel NICHT IN gesehen:
            ergebnis.anhängen(bereinigt)
            gesehen.hinzufügen(schlüssel)
    GIB ergebnis ZURÜCK
ENDE

FUNKTION baue_arxiv_url(schlagwörter, max_treffer, kategorien)
    EINGABE:  schlagwörter – normalisierte, nicht leere Liste
              max_treffer  – Anzahl gewünschter Dokumente, > 0
              kategorien   – Liste von arXiv-Kategorien, z. B. cs.SE, darf leer sein
    AUSGABE:  URL der arXiv-Abfrage

    WENN schlagwörter leer:
        FEHLER "Keine Schlagwörter"
    WENN max_treffer ≤ 0:
        FEHLER "max_treffer muss größer als 0 sein"

    suche ← jedes Schlagwort als all:"wort", verbunden mit OR
                                          // OR statt AND: mehr Treffer, die
                                          // Feinauswahl macht später BM25
    WENN kategorien nicht leer:
        filter ← jede Kategorie als cat:kategorie, verbunden mit OR
        suche  ← (suche) AND (filter)

    GIB Basis-URL + search_query=suche, start=0, max_results=max_treffer,
        sortBy=relevance, sortOrder=descending   (URL-kodiert) ZURÜCK
ENDE
