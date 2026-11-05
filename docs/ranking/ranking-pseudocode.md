FUNKTION reziproke_rang_fusion(ranglisten, k_rrf)
    EINGABE:  ranglisten – Liste von Ranglisten; jede Rangliste enthält
                           Kandidaten-IDs, bester Kandidat zuerst
              k_rrf      – Glättungskonstante, ≥ 0, üblich 60
    AUSGABE:  Liste von (id, score), höchster Score zuerst,
              bei Gleichstand kleinere id zuerst

    WENN k_rrf < 0:
        FEHLER "k_rrf darf nicht negativ sein"

    score ← leeres Wörterbuch
    FÜR JEDE rangliste IN ranglisten:
        FÜR JEDES (rang, id) IN rangliste, nummeriert ab 1:
            score[id] ← score[id] + 1 / (k_rrf + rang)
                                          // ein Kandidat, der nur in einer
                                          // Liste vorkommt, bekommt nur dort Punkte
    GIB score absteigend nach Wert sortiert ZURÜCK
ENDE
// Laufzeit: O(S + U · log U), S = Summe der Listenlängen, U = Anzahl verschiedener Kandidaten
// Nur Ränge zählen, nicht die Rohwerte: BM25-Scores und Cosinus-Werte haben verschiedene
// Skalen und werden so vergleichbar; Rechenbeispiel in der Formelsammlung


FUNKTION normalisiere_scores(scores)
    EINGABE:  scores – Liste von Zahlen
    AUSGABE:  Liste gleicher Länge mit Werten zwischen 0 und 1 (Min-Max)

    WENN scores leer:
        GIB leere Liste ZURÜCK
    WENN alle Werte gleich:
        GIB Liste mit lauter 1 ZURÜCK     // kein Kandidat ist schlechter
    GIB für jeden wert: (wert − minimum) / (maximum − minimum) ZURÜCK
ENDE
// Laufzeit: O(n)
