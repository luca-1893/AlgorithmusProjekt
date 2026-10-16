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
// Laufzeit: O(L), L = Gesamtlänge aller Schlagwörter; Nachschlagen in der Menge O(1)


STRUKTUR Suchfilter
    veröffentlicht_ab  – frühestes Datum der Erstveröffentlichung, LEER = keine Grenze
    veröffentlicht_bis – spätestes Datum, LEER = keine Grenze
    kategorien         – arXiv-Kategorien, leer = Standard der Quelle
    nur_begutachtet    – WAHR: nur Dokumente mit Zeitschriftenverweis oder DOI

    WENN veröffentlicht_ab > veröffentlicht_bis: FEHLER "Zeitraum ungültig"
ENDE
// Zeitraum und Kategorien filtert arXiv selbst, nur_begutachtet das Programm danach
// Bekannte Grenzen: Seitenzahl ist kein Filter, sie steht nur unregelmäßig im Kommentarfeld


FUNKTION baue_arxiv_url(schlagwörter, max_treffer, kategorien, ab, bis)
    EINGABE:  schlagwörter – normalisierte, nicht leere Liste
              max_treffer  – Anzahl gewünschter Dokumente, > 0
              kategorien   – Liste von arXiv-Kategorien, z. B. cs.SE, darf leer sein
              ab, bis      – Datumsgrenzen, beide dürfen LEER sein
    AUSGABE:  URL der arXiv-Abfrage

    WENN schlagwörter leer:
        FEHLER "Keine Schlagwörter"
    WENN max_treffer ≤ 0:
        FEHLER "max_treffer muss größer als 0 sein"

    suche ← jedes Schlagwort ohne Anführungszeichen als all:"wort",
            verbunden mit OR              // ein " im Wort würde die Phrase beenden
                                          // OR statt AND: mehr Treffer, die
                                          // Feinauswahl macht später BM25
    WENN kategorien nicht leer:
        filter ← jede Kategorie als cat:kategorie, verbunden mit OR
        suche  ← (suche) AND (filter)
    WENN ab oder bis gesetzt:
        suche ← suche AND submittedDate:[ab, sonst 1991-01-01, 00:00 TO bis, sonst 9999-12-31, 23:59]

    GIB Basis-URL + search_query=suche, start=0, max_results=max_treffer,
        sortBy=relevance, sortOrder=descending   (URL-kodiert) ZURÜCK
ENDE
// Laufzeit: O(L + K), K = Gesamtlänge der Kategorien
// Bekannte Grenzen: arXiv ist englischsprachig, deutsche Schlagwörter finden kaum etwas;
// OR liefert auch Dokumente, die nur ein Schlagwort enthalten


STRUKTUR Dokument
    id            – arXiv-Kennung ohne Versionsnummer, z. B. 1409.6928
    titel         – Titel, Leerraum vereinheitlicht
    abstract      – Zusammenfassung, Leerraum vereinheitlicht, darf leer sein
    autoren       – Liste der Autorennamen
    veröffentlicht – Datum der Erstveröffentlichung
    url           – Link auf die Abstract-Seite
    quelle        – Name der Quelle, hier "arxiv"
    kategorien    – arXiv-Kategorien, z. B. cs.SE, darf leer sein
    zeitschrift   – Zeitschriften- oder Konferenzverweis, leer bei reinen Preprints
    doi           – DOI, leer wenn keine vergeben
    begutachtet   – WAHR, wenn zeitschrift oder doi gesetzt ist
    text          – titel und abstract, durch eine Leerzeile getrennt
ENDE
// Unveränderlich nach dem Erzeugen; id dient später zur Duplikaterkennung in der Datenbank


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
        kategorien, zeitschrift, doi aus den Feldern category, arxiv:journal_ref, arxiv:doi
        dokumente.anhängen(Dokument aus den Feldern des Eintrags)
    GIB dokumente ZURÜCK                  // Feed ohne Einträge ergibt []
ENDE
// Laufzeit: O(X), X = Länge der Antwort; XML wird einmal vollständig gelesen


SCHNITTSTELLE Quelle
    name                                  – Name der Quelle, z. B. "arxiv"
    suche(schlagwörter, max_treffer, suchfilter) → Liste von Dokument
ENDE
// Jede weitere Quelle (OpenAlex, Semantic Scholar) setzt dieselbe Schnittstelle um;
// die Pipeline kennt nur die Schnittstelle


FUNKTION ArxivQuelle.suche(schlagwörter, max_treffer, suchfilter)
    EINGABE:  schlagwörter – Liste von Strings, roh vom LLM
              max_treffer  – Anzahl gewünschter Dokumente, > 0
              suchfilter   – Suchfilter oder LEER (dann keine Einschränkung)
    AUSGABE:  Liste von Dokument

    bereinigt ← normalisiere_schlagwörter(schlagwörter)
    abrufen   ← max_treffer · 3, WENN nur_begutachtet, SONST max_treffer
                                          // nach dem Filtern sollen genug übrig bleiben
    url       ← baue_arxiv_url(bereinigt, abrufen, kategorien des Filters, sonst der Quelle,
                               veröffentlicht_ab, veröffentlicht_bis)
                                          // wirft bei leeren Schlagwörtern,
                                          // bevor ein Netzwerkaufruf passiert
    VERSUCHE:
        antwort ← HTTP-GET url
    BEI Netzwerkfehler oder Zeitüberschreitung:
        FEHLER "Quelle nicht erreichbar"
    dokumente ← lies_arxiv_feed(antwort)
    WENN nur_begutachtet:
        dokumente ← nur die dokumente mit begutachtet = WAHR
    GIB die ersten max_treffer von dokumente ZURÜCK
ENDE
// Laufzeit: ein HTTP-Aufruf, dominiert von Netzwerk und Antwortgröße
// Bekannte Grenzen: nur Titel und Abstract (Volltext später); keine Drosselung zwischen
// mehreren Aufrufen, arXiv verlangt Abstand zwischen Anfragen; kein Cache (kommt mit PostgreSQL)
