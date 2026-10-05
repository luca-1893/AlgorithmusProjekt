flowchart TD
    Start([Start]) --> In[/Eingabe: raw_text, keywords, threshold/]
    
    In --> CheckInput{raw_text leer ODER<br/>keywords leer?}
    
    %% Fehlerpfad
    CheckInput -- Ja --> ErrorBox[Fehlermeldung ausgeben:<br/>'Ungültige Eingabe']
    ErrorBox --> EndError([Ende: Fehler])
    
    %% Hauptpfad Vorbereitung
    CheckInput -- Nein --> Prep[Text in Einzelsätze zerlegen &<br/>Keywords normalisieren / Kleinschreibung]
    Prep --> LoopCheck{Gibt es noch<br/>ungeprüfte Sätze?}
    
    %% Schleife
    LoopCheck -- Ja --> ProcessSentence[Nächsten Satz analysieren:<br/>Treffer der Keywords zählen &<br/>Score = Treffer / Satzlänge berechnen]
    ProcessSentence --> ScoreCheck{Score >= threshold?}
    
    ScoreCheck -- Ja --> AddList[Satz zur Liste<br/>'Relevante Sätze' hinzufügen]
    AddList --> LoopCheck
    
    ScoreCheck -- Nein --> LoopCheck
    
    %% Nach der Schleife
    LoopCheck -- Nein --> EmptyCheck{Ist Liste<br/>'Relevante Sätze'<br/>leer?}
    
    EmptyCheck -- Ja --> Fallback[Fallback: Satz mit absolut<br/>höchstem Score wählen +<br/>Warnhinweis 'Kein Schwellenwert-Treffer' setzen]
    EmptyCheck -- Nein --> BuildText
    Fallback --> BuildText
    
    BuildText[Ausgewählte Sätze zusammenfügen &<br/>Token-/Zeichenersparnis in % berechnen]
    BuildText --> Out[/Ausgabe: Optimierter Text & Metriken/]
    Out --> EndSuccess([Ende: Erfolg])
