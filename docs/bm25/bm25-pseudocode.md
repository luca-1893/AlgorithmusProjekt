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
