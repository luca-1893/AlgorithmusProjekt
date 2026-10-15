FUNKTION tokenisiere(text)
    EINGABE:  text – roher String, deutscher oder englischer Fließtext
    AUSGABE:  Liste der Wörter, kleingeschrieben, ohne Satzzeichen,
              NICHT dedupliziert

    VERBINDER ← Bindestrich (-), Apostrophe (' ’)
                // Gedankenstriche (– —) sind keine Verbinder: sie trennen
                // wie Satzzeichen (10–20 → 10, 20)

    klein     ← text in Kleinbuchstaben (casefold)
    verbunden ← in klein jeden VERBINDER ersatzlos entfernen
    bereinigt ← in verbunden jedes Zeichen, das kein Buchstabe und keine
                Ziffer ist, durch ein Leerzeichen ersetzen
    wörter    ← bereinigt an Leerraum aufteilen
    GIB wörter ZURÜCK                     // leerer Text ergibt []
ENDE


FUNKTION baue_index(korpus)
    EINGABE:  korpus – Liste von Texten (ein Text = ein Dokument/Chunk)
    AUSGABE:  index  – Zuordnung Wort → (Dok-ID → Anzahl)
              laenge – Zuordnung Dok-ID → Anzahl Tokens
              N      – Anzahl nicht-leerer Dokumente
              avgdl  – durchschnittliche Dokumentlänge (0 bei leerem Korpus)

    index  ← leeres Dict
    laenge ← leeres Dict

    FÜR i VON 0 BIS len(korpus) - 1:              // Dok-ID = Position in korpus
        dok    ← korpus[i]
        tokens ← tokenisiere(dok)
        WENN tokens ist leer:                     // leeres Dokument überspringen,
            WEITER                                // IDs der anderen bleiben stabil

        laenge[i] ← len(tokens)

        FÜR JEDES wort IN tokens:
            WENN wort NICHT IN index:
                index[wort] ← leeres Dict
            WENN i NICHT IN index[wort]:
                index[wort][i] ← 1
            SONST:
                index[wort][i] ← index[wort][i] + 1

    N ← len(laenge)
    WENN N = 0:
        avgdl ← 0                                 // Score muss leeren Index vorher abfangen
    SONST:
        avgdl ← summe(laenge.werte) / N

    RÜCKGABE index, laenge, N, avgdl
ENDE
// Laufzeit: O(T), T = Anzahl aller Tokens im Korpus (streng: O(C), C = Zeichen)
// k1, b und K gehören nicht in den Index, sondern zur Suche


FUNKTION berechne_idf(df, N)
    EINGABE:  df – Dokumenthäufigkeit n(q): in wie vielen Dokumenten das Wort vorkommt
                   (Aufrufer: df ← len(index.get(wort, {})), unbekanntes Wort ergibt 0)
              N  – Anzahl nicht-leerer Dokumente (N = 0 fängt der Aufrufer vorher ab)
    AUSGABE:  idf – Gewicht des Worts (immer > 0)

    idf ← ln( (N - df + 0.5) / (df + 0.5) + 1 )
    RÜCKGABE idf
ENDE
// Variante mit +1 (Lucene): Argument von ln ist immer > 1, daher nie negativ.
// Klassische Variante ohne +1 wird negativ, sobald df > N/2.
// Laufzeit: O(1)


FUNKTION berechne_beitrag(f, dl, avgdl, idf, k1, b)
    EINGABE:  f     – Häufigkeit des Worts im Dokument
              dl    – Länge des Dokuments (Anzahl Tokens)
              avgdl – durchschnittliche Dokumentlänge (> 0)
              idf   – Gewicht des Worts
              k1    – Sättigung der Termfrequenz (z. B. 1.5)
              b     – Stärke der Längennormalisierung (z. B. 0.75)
    AUSGABE:  beitrag – Anteil dieses Worts am Score (≥ 0, 0 bei f = 0)

    L       ← dl / avgdl
    K       ← k1 · (1 − b + b · L)
    TF      ← f · (k1 + 1) / (f + K)
    beitrag ← idf · TF

    RÜCKGABE beitrag
ENDE
// Laufzeit: O(1)


FUNKTION berechne_score(query, doc_id, index, laenge, N, avgdl, k1, b)
    EINGABE:  query  – Menge von Query-Wörtern; der Aufrufer tokenisiert die Anfrage
                       und entfernt Duplikate (doppelte Schlagwörter sind eher Zufall
                       oder Halluzination, die Formel braucht keine Anfrage-Häufigkeit)
              doc_id – Dokument, das bewertet wird
              index  – Zuordnung Wort → (Dok-ID → Anzahl)
              laenge – Zuordnung Dok-ID → Anzahl Tokens
              N      – Anzahl nicht-leerer Dokumente
              avgdl  – durchschnittliche Dokumentlänge
              k1, b  – BM25-Parameter
    AUSGABE:  score  – Relevanz des Dokuments für die Anfrage (≥ 0)

    WENN N = 0:                                   // leerer Index: avgdl = 0,
        RÜCKGABE 0                                // Division durch null vermeiden

    WENN doc_id NICHT IN laenge:                  // leeres (übersprungenes) oder
        RÜCKGABE 0                                // unbekanntes Dokument

    dl    ← laenge[doc_id]
    score ← 0

    FÜR JEDES wort IN query:
        posting ← index.get(wort, {})
        f       ← posting.get(doc_id, 0)          // Wort nicht im Dokument → f = 0
        idf     ← berechne_idf(len(posting), N)
        score   ← score + berechne_beitrag(f, dl, avgdl, idf, k1, b)

    RÜCKGABE score
ENDE
// Laufzeit: O(|query|) pro Dokument, jeder Schritt ist ein Dict-Zugriff
// Offen für Schritt 7: IDF hängt nur am Wort und wird hier pro Dokument neu berechnet


FUNKTION top_m(anfrage, index, laenge, N, avgdl, m, k1, b)
    EINGABE:  anfrage – roher Anfrage-String (Schlagwörter)
              index, laenge, N, avgdl – Ergebnis von baue_index
              m       – Anzahl gewünschter Treffer
              k1, b   – BM25-Parameter
    AUSGABE:  Liste von (doc_id, score), höchster Score zuerst,
              bei Gleichstand kleinere doc_id zuerst; höchstens m Einträge,
              nur Dokumente mit score > 0

    WENN N = 0 ODER m ≤ 0:                        // leerer Index / nichts verlangt
        RÜCKGABE leere Liste

    query ← Menge(tokenisiere(anfrage))           // nach dem Tokenisieren deduplizieren

    idfs ← leeres Dict                            // IDF einmal pro Wort, nicht pro Dokument
    FÜR JEDES wort IN query:
        idfs[wort] ← berechne_idf(len(index.get(wort, {})), N)

    kandidaten ← leere Menge                      // nur Dokumente mit mindestens einem
    FÜR JEDES wort IN query:                      // Anfragewort → score > 0 automatisch
        kandidaten ← kandidaten ∪ Dok-IDs in index.get(wort, {})

    bewertet ← leere Liste
    FÜR JEDE doc_id IN kandidaten:
        score ← berechne_score(query, doc_id, index, laenge, idfs, avgdl, k1, b)
        FÜGE (−score, doc_id) ZU bewertet HINZU   // −score: höchster Score wird "kleinster"

    beste ← die m kleinsten Einträge aus bewertet (Heap, nsmallest)
                                                  // Gleichstand: kleinere doc_id zuerst
    RÜCKGABE [(doc_id, −neg_score) FÜR JEDES (neg_score, doc_id) IN beste]
ENDE
// Laufzeit (C = Anzahl Kandidaten, |q| = Anfragewörter, P = Summe der Posting-Längen):
//   IDFs:               O(|q|)
//   Kandidaten sammeln: O(P)
//   bewerten:           O(C · |q|)
//   Top-m per Heap:     O(C · log m)   statt O(C · log C) beim kompletten Sortieren
