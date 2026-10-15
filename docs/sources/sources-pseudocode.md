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

STRUKTUR Dokument
    id            – arXiv-Kennung ohne Versionsnummer, z. B. 1409.6928
    titel         – Titel, Leerraum vereinheitlicht
    abstract      – Zusammenfassung, Leerraum vereinheitlicht, darf leer sein
    autoren       – Liste der Autorennamen
    veröffentlicht – Datum der Erstveröffentlichung
    url           – Link auf die Abstract-Seite
    quelle        – Name der Quelle, hier "arxiv"
    text          – titel und abstract, durch eine Leerzeile getrennt
ENDE

FUNKTION lies_arxiv_feed(xml_text)
    EINGABE:  xml_text – Antwort der arXiv-API (Atom-Feed)
    AUSGABE:  Liste von Dokument, in der Reihenfolge des Feeds

    WENN xml_text kein gültiges XML:
        FEHLER "Antwort der Quelle nicht lesbar"

    dokumente ← leere Liste
    FÜR JEDEN eintrag IN feed:
        WENN eintrag.id beginnt mit der Fehler-Adresse der API:
            FEHLER "Quelle meldet Fehler: " + eintrag.summary
        WENN id, titel ODER veröffentlicht fehlen:
            WEITER                        // unvollständigen Eintrag überspringen
        id ← Teil nach "/abs/", Versionsendung "vN" entfernt
        dokumente.anhängen(Dokument aus den Feldern des Eintrags)
    GIB dokumente ZURÜCK                  // Feed ohne Einträge ergibt []
ENDE

SCHNITTSTELLE Quelle
    name                                  – Name der Quelle, z. B. "arxiv"
    suche(schlagwörter, max_treffer) → Liste von Dokument
ENDE

FUNKTION ArxivQuelle.suche(schlagwörter, max_treffer)
    EINGABE:  schlagwörter – Liste von Strings, roh vom LLM
              max_treffer  – Anzahl gewünschter Dokumente, > 0
    AUSGABE:  Liste von Dokument

    bereinigt ← normalisiere_schlagwörter(schlagwörter)
    url       ← baue_arxiv_url(bereinigt, max_treffer, kategorien der Quelle)
                                          // wirft bei leeren Schlagwörtern,
                                          // bevor ein Netzwerkaufruf passiert
    VERSUCHE:
        antwort ← HTTP-GET url
    BEI Netzwerkfehler oder Zeitüberschreitung:
        FEHLER "Quelle nicht erreichbar"
    GIB lies_arxiv_feed(antwort) ZURÜCK
ENDE
