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
