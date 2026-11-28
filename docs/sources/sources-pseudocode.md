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
    herkunft      – woher der Text stammt: "html", "pdf" oder "abstract" (Standard)
    volltext      – extrahierter Volltext, leer genau dann, wenn herkunft = "abstract"
    text          – titel und volltext, WENN volltext nicht leer,
                    SONST titel und abstract; jeweils durch eine Leerzeile getrennt
ENDE
// Unveränderlich nach dem Erzeugen; id dient später zur Duplikaterkennung in der Datenbank
// herkunft und volltext müssen zusammenpassen, sonst FEHLER (wie documents_invalid_full_text im Schema)


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
    volltext                              – WAHR: Dokumente kommen mit Volltext, wo möglich (R17)
    hinweise                              – Hinweise des letzten Aufrufs, z. B. zum Volltext-Rückfall
    suche(schlagwörter, max_treffer, suchfilter) → Liste von Dokument
    ergänze_volltexte(dokumente) → Liste von Dokument
                                          // Standard: unverändert zurück (Quelle ohne Volltext)
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
    WENN volltext:
        warte, bis seit der letzten Anfrage des Volltextabrufs pause vergangen ist
                                          // dieselbe Pause wie für die Downloads, gleicher Server
    VERSUCHE:
        antwort ← HTTP-GET url
    BEI Netzwerkfehler oder Zeitüberschreitung:
        FEHLER "Quelle nicht erreichbar"
    dokumente ← lies_arxiv_feed(antwort)
    WENN nur_begutachtet:
        dokumente ← nur die dokumente mit begutachtet = WAHR
    dokumente ← die ersten max_treffer von dokumente
    WENN volltext:
        dokumente ← ergänze_volltexte(dokumente)          // R17
    GIB dokumente ZURÜCK
ENDE
// Laufzeit: ein HTTP-Aufruf, dominiert von Netzwerk und Antwortgröße;
// mit Volltext zusätzlich ein bis zwei Downloads pro Dokument (siehe unten)
// Bekannte Grenzen: ohne Volltext nur Titel und Abstract; der Cache liegt davor (docs/cache/)


## Volltext (R17, ADR 0006)

FUNKTION html_text(html)
    EINGABE:  html – HTML-Seite eines Papers (arXiv erzeugt sie mit LaTeXML)
    AUSGABE:  Fließtext aus <article>, Leerraum vereinheitlicht

    teile ← leere Liste
    überspringen ← 0                       // Tiefe innerhalb eines übersprungenen Elements
    FÜR JEDES Start-Tag, End-Tag und Textstück in html, in Reihenfolge:
        leere Elemente (br, img, …) zählen nicht zur Tiefe
        WENN überspringen > 0: Tiefe mitzählen, Text verwerfen
        SONST WENN innerhalb von <article> UND (Tag ist script, style, math, nav, header, footer,
                   svg, figure, table ODER Klasse enthält Literaturverzeichnis, Kopf-, Fußzeile,
                   Autoren oder Fußnote):
            überspringen ← 1
        SONST WENN Text innerhalb von <article>: teile.anhängen(Text)
        Ende von p, div, section, h1–h4, li: Zeilenumbruch anhängen
    GIB teile verbunden, Leerraum auf ein Leerzeichen reduziert ZURÜCK
ENDE
// Laufzeit: O(H), H = Länge der Seite, ein Durchlauf
// Formeln fallen weg (sie bestehen aus Zeichen, nicht aus Wörtern); Tabellen und Abbildungen auch


FUNKTION schneide_literatur_ab(text)
    treffer ← letzte Zeile, die nur "References" oder "Bibliography" enthält (beliebige Schreibweise groß/klein)
    WENN treffer existiert UND treffer in der zweiten Hälfte von text liegt:
        GIB text bis vor treffer ZURÜCK
    GIB text ZURÜCK
ENDE
// Zweite Hälfte: ein "References" im Inhaltsverzeichnis oder in der Einleitung schneidet nichts ab


FUNKTION pdf_text(pdf_bytes)
    text ← Text aller Seiten mit pypdf, durch Zeilenumbrüche getrennt
    text ← schneide_literatur_ab(text)
    text ← Trennstriche am Zeilenende entfernen ("Algo-\nrithmus" → "Algorithmus")
    GIB text mit vereinheitlichtem Leerraum ZURÜCK
ENDE
// Wenn die Bibliothek fehlt oder die Datei kaputt ist: FEHLER "PDF nicht lesbar"


KLASSE Volltextabruf
    abrufen      – HTTP-GET, liefert (Inhalt, Inhaltstyp); austauschbar für Tests
    schlafen     – Wartefunktion; austauschbar für Tests
    pause        – Mindestabstand zwischen zwei Anfragen an arXiv, 3,1 s
    versuche     – höchstens 4 Versuche pro URL
    wartezeit    – erste Wartezeit nach HTTP 429, 5 s, verdoppelt sich pro Versuch
    gedrosselt   – WAHR, sobald eine URL nach allen Versuchen noch 429 bekam
ENDE


FUNKTION Volltextabruf.hole(url)
    AUSGABE:  (Inhalt, Inhaltstyp) oder LEER
    FÜR versuch VON 1 BIS versuche:
        warte, bis seit der letzten Anfrage pause vergangen ist
        VERSUCHE:
            GIB abrufen(url) ZURÜCK
        BEI HTTP 429 oder 503:
            WENN versuch < versuche: schlafen(wartezeit · 2^(versuch − 1))   // 5, 10, 20 s
        BEI anderem HTTP-Fehler (z. B. 404: keine HTML-Fassung), Netzwerkfehler, Zeitüberschreitung:
            GIB LEER ZURÜCK
    gedrosselt ← WAHR
    GIB LEER ZURÜCK
ENDE
// Laufzeit: höchstens versuche Anfragen; im schlimmsten Fall 5 + 10 + 20 = 35 s Warten pro URL


FUNKTION Volltextabruf.volltext(arxiv_id)
    AUSGABE:  (herkunft, text) oder LEER
    antwort ← hole(HTML-URL der id)
    WENN antwort ist HTML:
        text ← html_text(antwort)
        WENN Anzahl Wörter von text ≥ 500: GIB ("html", text) ZURÜCK
    WENN gedrosselt: GIB LEER ZURÜCK
    antwort ← hole(PDF-URL der id)
    WENN antwort beginnt mit "%PDF":
        VERSUCHE: text ← pdf_text(antwort)
        BEI "PDF nicht lesbar": GIB LEER ZURÜCK
        WENN Anzahl Wörter von text ≥ 500: GIB ("pdf", text) ZURÜCK
    GIB LEER ZURÜCK
ENDE
// Unter 500 Wörtern ist die Extraktion gescheitert (z. B. Fehlerseite statt Paper);
// dann ist das Abstract der bessere Text


FUNKTION ArxivQuelle.ergänze_volltexte(dokumente)
    hinweise ← leere Liste
    volltextabruf.gedrosselt ← FALSCH
    ergebnis ← leere Liste
    fehlend  ← leere Liste
    FÜR JEDES dokument IN dokumente:
        treffer ← LEER, WENN volltextabruf.gedrosselt, SONST volltextabruf.volltext(dokument.id)
        WENN treffer LEER:
            ergebnis.anhängen(dokument)                       // R17: Abstract bleibt
            fehlend.anhängen(dokument.id)
        SONST:
            ergebnis.anhängen(dokument mit herkunft und volltext aus treffer)
    WENN fehlend nicht leer:
        hinweise.anhängen("Volltext nicht verfügbar für <Anzahl> von <Anzahl> Dokumenten,
                           dort nur Titel und Abstract: <ids>")
    WENN volltextabruf.gedrosselt:
        hinweise.anhängen("arXiv drosselt (HTTP 429), weitere Volltexte übersprungen")
    GIB ergebnis ZURÜCK
ENDE
// Laufzeit: pro Dokument eine (HTML) oder zwei (PDF) Anfragen mit 3,1 s Abstand,
// bei 20 Dokumenten also mindestens etwa eine Minute, wenn nichts im Cache liegt
// Anfragen laufen nacheinander, nie parallel (arXiv-Nutzungsregeln)
// Bekannte Grenzen: Ist arXiv gedrosselt, bekommen die übrigen Dokumente dieses Aufrufs nur
// das Abstract; der nächste Aufruf versucht es wieder
