STRUKTUR Konfiguration
    max_dokumente – wie viele Dokumente die Quelle höchstens liefern soll    (20)
    chunk_größe   – Wörter pro Chunk                                         (200)
    überlappung   – gemeinsame Wörter benachbarter Chunks                    (40)
    m             – Kandidaten aus der BM25-Vorauswahl                       (50)
    k_rrf         – Glättungskonstante der Rangfusion                        (60)
    lambda        – MMR-Gewicht Relevanz gegen Vielfalt                      (0.7)
ENDE


STRUKTUR Treffer
    dokument – Dokument mit Metadaten (Titel, Autoren, Datum, Link)
    chunk    – Chunk mit Position und Text
    score    – BM25-Score im Pfad ohne Vektorsuche, RRF-Score im hybriden Pfad
ENDE


STRUKTUR Ergebnis
    treffer   – Liste von Treffer, bester zuerst
    hinweise  – Liste von Texten, z. B. "Keine Treffer" oder ein Fallback
ENDE
// Wird für das MCP-Tool als JSON ausgegeben


FUNKTION recherchiere(schlagwörter, k, quelle, einbetter, frage, konfiguration, suchfilter)
    EINGABE:  schlagwörter – Liste von Strings, roh vom LLM
              k            – Anzahl gewünschter Treffer, > 0
              quelle       – eine Quelle, z. B. ArxivQuelle
              einbetter    – ein Einbetter oder LEER (dann ohne Vektorsuche)
              frage        – ursprüngliche Frage für die Vektorsuche, darf leer sein
              konfiguration
              suchfilter   – Suchfilter oder LEER, wird an die Quelle weitergereicht
    AUSGABE:  Ergebnis

    WENN k ≤ 0: FEHLER "k muss größer als 0 sein"
    schlagwörter ← normalisiere_schlagwörter(schlagwörter)
    WENN schlagwörter leer: FEHLER "Keine Schlagwörter"

    dokumente ← quelle.suche(schlagwörter, max_dokumente, suchfilter)   // Quellenfehler gehen an den Aufrufer
    WENN dokumente leer: RÜCKGABE Ergebnis([], ["Keine Treffer"])

    chunks ← leere Liste
    FÜR JEDES dokument IN dokumente:
        FÜR JEDEN chunk IN erzeuge_chunks(dokument.id, dokument.text, chunk_größe, überlappung):
            chunks.anhängen((chunk, dokument))
    WENN chunks leer: RÜCKGABE Ergebnis([], ["Keine verwertbaren Quellen"])

    index, laenge, N, avgdl ← baue_index(Texte aller chunks)   // Dok-ID = Position in chunks
    bm25 ← top_m(schlagwörter mit Leerzeichen verbunden, index, laenge, N, avgdl, m)

    WENN einbetter LEER:
        RÜCKGABE nur_bm25(bm25, chunks, k)
    RÜCKGABE hybrid(bm25, chunks, k, einbetter, frage, schlagwörter, konfiguration)
ENDE
// Laufzeit: dominiert von Quelle (Netzwerk) und Einbetter (API); lokal O(T) für Chunking
// und Index, T = Wörter aller Dokumente


FUNKTION nur_bm25(bm25, chunks, k)
    WENN bm25 leer: RÜCKGABE Ergebnis([], ["Kein Chunk enthält ein Schlagwort"])
    RÜCKGABE Ergebnis(die ersten k von bm25 als Treffer mit BM25-Score, [])
ENDE
// Laufzeit: O(k)


FUNKTION hybrid(bm25, chunks, k, einbetter, frage, schlagwörter, konfiguration)
    WENN bm25 leer:
        kandidaten ← alle Positionen in chunks          // kein Chunk enthält ein Schlagwort:
        bm25_rangliste ← leer                           // alle bleiben Kandidaten, nur die
    SONST:                                              // Vektorsuche entscheidet
        kandidaten ← Positionen aus bm25, in BM25-Reihenfolge
        bm25_rangliste ← 0, 1, …, Anzahl(kandidaten) − 1

    anfrage ← frage, falls nicht leer, sonst schlagwörter mit Leerzeichen verbunden
    VERSUCHE:
        anfrage_vektor      ← einbetter.einbetten([anfrage], "query")[0]
        kandidaten_vektoren ← einbetter.einbetten(Texte der kandidaten, "document")
    BEI Einbettungsfehler:
        ergebnis ← nur_bm25(bm25, chunks, k)
        RÜCKGABE ergebnis mit zusätzlichem Hinweis "Vektorsuche nicht verfügbar, nur BM25"

    vektor_rangliste ← Positionen aus ähnlichste(anfrage_vektor, kandidaten_vektoren, Anzahl(kandidaten))

    fusion ← reziproke_rang_fusion([bm25_rangliste, vektor_rangliste], k_rrf)
    relevanz ← normalisiere_scores(Scores aus fusion)
    auswahl ← mmr_auswahl(relevanz, Vektoren in fusion-Reihenfolge, k, lambda)

    RÜCKGABE Ergebnis(für jede gewählte Stelle: Treffer mit RRF-Score, [])
ENDE
// Laufzeit: zwei Einbettungsaufrufe (Anfrage, m Kandidaten); lokal O(m · d) für die Ähnlichkeiten,
// O(m · log m) für die Fusion und O(k · m · d) für MMR
// Bekannte Grenzen: Fällt der Einbetter aus, sinkt die Qualität still auf BM25; der Hinweis
// im Ergebnis ist das einzige Signal dafür
