FUNKTION tokenisiere(text)
    EINGABE:  text – roher String, deutscher oder englischer Fließtext
    AUSGABE:  Liste der Wörter, kleingeschrieben, ohne Satzzeichen,
              NICHT dedupliziert

    VERBINDER ← Bindestrich (-), Gedankenstriche (– —), Apostrophe (' ’)

    klein     ← text in Kleinbuchstaben (casefold)
    verbunden ← in klein jeden VERBINDER ersatzlos entfernen
    bereinigt ← in verbunden jedes Zeichen, das kein Buchstabe und keine
                Ziffer ist, durch ein Leerzeichen ersetzen
    wörter    ← bereinigt an Leerraum aufteilen
    GIB wörter ZURÜCK                     // leerer Text ergibt []
ENDE
