FUNKTION tokenisiere(text)
    EINGABE:  text – roher String, deutscher oder englischer Fließtext
    AUSGABE:  Liste der Wörter, kleingeschrieben, ohne Satzzeichen,
              NICHT dedupliziert

    klein     ← text in Kleinbuchstaben (lower)
    getrennt  ← in klein jeden Bindestrich durch ein Leerzeichen ersetzen
    bereinigt ← nur die Zeichen aus getrennt behalten,
                die Buchstabe, Ziffer oder Leerzeichen sind
    wörter    ← bereinigt an Leerraum aufteilen
    GIB wörter ZURÜCK                     // leerer Text ergibt []
ENDE