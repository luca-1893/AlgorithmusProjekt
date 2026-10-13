FUNKTION tokenisiere(text)
    EINGABE:  text – roher String, deutscher oder englischer Fließtext
    AUSGABE:  Liste der Wörter, kleingeschrieben, ohne Satzzeichen,
              NICHT dedupliziert

    klein     ← text in Kleinbuchstaben (casefold)
    verbunden ← in klein jeden Bindestrich entfernen, der direkt zwischen
                zwei Buchstaben/Ziffern steht
    bereinigt ← in verbunden jedes Zeichen, das kein Buchstabe und keine
                Ziffer ist, durch ein Leerzeichen ersetzen
    wörter    ← bereinigt an Leerraum aufteilen
    GIB wörter ZURÜCK                     // leerer Text ergibt []
ENDE



