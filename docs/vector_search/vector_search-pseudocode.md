FUNKTION cosinus_ähnlichkeit(a, b)
    EINGABE:  a, b – Vektoren (Listen von Zahlen) gleicher, nicht leerer Länge
    AUSGABE:  Zahl zwischen −1 und 1; 1 heißt gleiche Richtung

    WENN Länge(a) ≠ Länge(b) ODER Länge(a) = 0:
        FEHLER "Vektoren müssen gleich lang und nicht leer sein"

    skalarprodukt ← Summe über i von a[i] · b[i]
    länge_a       ← Wurzel aus Summe über i von a[i]²
    länge_b       ← Wurzel aus Summe über i von b[i]²
    WENN länge_a = 0 ODER länge_b = 0:
        GIB 0 ZURÜCK                      // Nullvektor hat keine Richtung,
                                          // also keine Ähnlichkeit
    GIB skalarprodukt / (länge_a · länge_b) ZURÜCK
ENDE

FUNKTION top_k(scores, k)
    EINGABE:  scores – Liste von Zahlen, Position i gehört zu Kandidat i
              k      – Anzahl gewünschter Kandidaten, > 0
    AUSGABE:  Liste von (position, score), höchster Score zuerst,
              bei Gleichstand kleinere Position zuerst

    WENN k ≤ 0:
        FEHLER "k muss größer als 0 sein"

    heap ← leerer Min-Heap                // enthält höchstens k Einträge,
                                          // oben liegt der schwächste davon
    FÜR JEDES (position, score) IN scores:
        eintrag ← (score, −position)      // bei Gleichstand ist die größere
                                          // Position der schwächere Eintrag
        WENN Größe(heap) < k:
            heap.einfügen(eintrag)
        SONST WENN eintrag > heap.oberstes:
            heap.oberstes ersetzen durch eintrag

    GIB heap absteigend sortiert, als (position, score) ZURÜCK
ENDE                                      // Laufzeit O(n · log k) statt
                                          // O(n · log n) für vollständiges Sortieren

FUNKTION ähnlichste(anfrage_vektor, kandidaten_vektoren, k)
    EINGABE:  anfrage_vektor      – Vektor der Anfrage
              kandidaten_vektoren – Liste von Vektoren, gleiche Länge wie anfrage_vektor
              k                   – Anzahl gewünschter Kandidaten, > 0
    AUSGABE:  Liste von (position, ähnlichkeit), ähnlichster Kandidat zuerst

    ähnlichkeiten ← für jeden kandidat: cosinus_ähnlichkeit(anfrage_vektor, kandidat)
    GIB top_k(ähnlichkeiten, k) ZURÜCK
ENDE                                      // Laufzeit O(n · d + n · log k),
                                          // d = Vektorlänge

SCHNITTSTELLE Einbetter
    anbieter_anfrage(texte) → Liste von Vektoren   // je Anbieter umzusetzen, siehe ADR 0001
ENDE

FUNKTION Einbetter.einbetten(texte)
    EINGABE:  texte – Liste von Strings
    AUSGABE:  Liste von Vektoren, einer pro Text, gleiche Reihenfolge

    WENN texte leer:
        GIB leere Liste ZURÜCK            // kein API-Aufruf ohne Inhalt

    vektoren ← anbieter_anfrage(texte)
    WENN Anzahl(vektoren) ≠ Anzahl(texte):
        FEHLER "Anbieter lieferte falsche Anzahl Vektoren"
    WENN ein Vektor leer ist ODER die Vektoren unterschiedlich lang sind:
        FEHLER "Anbieter lieferte ungültige Vektoren"
    GIB vektoren ZURÜCK
ENDE
