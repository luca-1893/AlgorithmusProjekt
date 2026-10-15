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
// Laufzeit: O(d), d = Vektorlänge; Formeln und Rechenbeispiel in der Formelsammlung


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
ENDE
// Laufzeit O(n · log k) statt O(n · log n) für vollständiges Sortieren


FUNKTION ähnlichste(anfrage_vektor, kandidaten_vektoren, k)
    EINGABE:  anfrage_vektor      – Vektor der Anfrage
              kandidaten_vektoren – Liste von Vektoren, gleiche Länge wie anfrage_vektor
              k                   – Anzahl gewünschter Kandidaten, > 0
    AUSGABE:  Liste von (position, ähnlichkeit), ähnlichster Kandidat zuerst

    ähnlichkeiten ← für jeden kandidat: cosinus_ähnlichkeit(anfrage_vektor, kandidat)
    GIB top_k(ähnlichkeiten, k) ZURÜCK
ENDE
// Laufzeit O(n · d + n · log k), d = Vektorlänge


SCHNITTSTELLE Einbetter
    anbieter_anfrage(texte, art) → Liste von Vektoren   // je Anbieter umzusetzen, siehe ADR 0001
ENDE


FUNKTION Einbetter.einbetten(texte, art)
    EINGABE:  texte – Liste von Strings
              art   – "query" für die Anfrage, "document" für Chunks (Standard);
                      Anbieter wie Voyage betten beides unterschiedlich ein
    AUSGABE:  Liste von Vektoren, einer pro Text, gleiche Reihenfolge

    WENN art weder "query" noch "document": FEHLER "Ungültige Art"

    WENN texte leer:
        GIB leere Liste ZURÜCK            // kein API-Aufruf ohne Inhalt

    vektoren ← anbieter_anfrage(texte, art)
    WENN Anzahl(vektoren) ≠ Anzahl(texte):
        FEHLER "Anbieter lieferte falsche Anzahl Vektoren"
    WENN ein Vektor leer ist ODER die Vektoren unterschiedlich lang sind:
        FEHLER "Anbieter lieferte ungültige Vektoren"
    GIB vektoren ZURÜCK
ENDE
// Laufzeit: ein API-Aufruf für alle Texte zusammen, nicht einer pro Text
// Bekannte Grenzen: Anbieter noch offen (ADR 0001); kein Wiederholen bei Netzwerkfehlern


FUNKTION mmr_auswahl(relevanz, vektoren, k, lambda)
    EINGABE:  relevanz – Liste von Zahlen zwischen 0 und 1, eine pro Kandidat
              vektoren – Liste von Vektoren, einer pro Kandidat
              k        – Anzahl auszuwählender Kandidaten, > 0
              lambda   – Gewicht zwischen 0 und 1; 1 heißt nur Relevanz,
                         0 heißt nur Vielfalt
    AUSGABE:  Liste der ausgewählten Positionen, in Auswahlreihenfolge

    WENN Anzahl(relevanz) ≠ Anzahl(vektoren): FEHLER "Längen passen nicht"
    WENN k ≤ 0 ODER lambda außerhalb [0, 1]:  FEHLER "Ungültige Parameter"

    ausgewählt ← leere Liste
    übrig      ← alle Positionen
    SOLANGE übrig nicht leer UND Anzahl(ausgewählt) < k:
        bester ← die Position p aus übrig mit dem höchsten Wert
                 lambda · relevanz[p] − (1 − lambda) · ähnlichkeit_zur_auswahl(p)
                 wobei ähnlichkeit_zur_auswahl(p) = höchste Cosinus-Ähnlichkeit
                 von vektoren[p] zu einem bereits ausgewählten Vektor, 0 wenn
                 noch nichts ausgewählt ist
                 (bei Gleichstand die kleinere Position)
        ausgewählt.anhängen(bester)
        übrig.entfernen(bester)
    GIB ausgewählt ZURÜCK
ENDE
// Laufzeit O(k · n · d) mit n Kandidaten und Vektorlänge d, weil die höchste Ähnlichkeit pro Kandidat nach jeder Wahl nur um den neuen Vektor aktualisiert wird
