FUNKTION zerlege_in_chunks(text, chunk_größe, überlappung)
    EINGABE:  text          – roher String, z. B. ein normalisiertes Dokument
              chunk_größe   – Anzahl Wörter pro Chunk, > 0
              überlappung   – Anzahl Wörter, die zwei aufeinanderfolgende
                              Chunks gemeinsam haben, 0 ≤ überlappung < chunk_größe
    AUSGABE:  Liste der Chunks als Strings, Wörter durch genau ein
              Leerzeichen getrennt

    WENN chunk_größe ≤ 0 ODER überlappung < 0 ODER überlappung ≥ chunk_größe:
        FEHLER "Ungültige Parameter"      // sonst käme die Schleife nie voran

    wörter    ← text an Leerraum aufteilen
    schritt   ← chunk_größe − überlappung
    chunks    ← leere Liste
    start     ← 0

    SOLANGE start < Anzahl(wörter):
        ende ← start + chunk_größe
        chunks.anhängen(wörter[start .. ende−1] mit Leerzeichen verbinden)
        WENN ende ≥ Anzahl(wörter):
            ABBRUCH                       // letzter Chunk erreicht das Textende;
                                          // ein weiterer bestünde nur aus Überlappung
        start ← start + schritt

    GIB chunks ZURÜCK                     // leerer Text ergibt []
ENDE

STRUKTUR Chunk
    dokument_id – Kennung des Quelldokuments, z. B. arXiv-ID
    position    – laufende Nummer des Chunks im Dokument, beginnt bei 0
    text        – Inhalt des Chunks
ENDE

FUNKTION erzeuge_chunks(dokument_id, text, chunk_größe, überlappung)
    EINGABE:  dokument_id   – nicht leerer String
              text, chunk_größe, überlappung – wie bei zerlege_in_chunks
    AUSGABE:  Liste von Chunk, in der Reihenfolge des Textes

    WENN dokument_id leer:
        FEHLER "Dokument-ID fehlt"

    texte  ← zerlege_in_chunks(text, chunk_größe, überlappung)
    chunks ← leere Liste
    FÜR JEDES (position, chunk_text) IN texte, nummeriert ab 0:
        chunks.anhängen(Chunk(dokument_id, position, chunk_text))

    GIB chunks ZURÜCK                     // die übrigen Metadaten bleiben am
                                          // Dokument, verknüpft über dokument_id
ENDE
