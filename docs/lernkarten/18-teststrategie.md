# 18 Teststrategie

**In einem Satz:** 325 Unittests in drei Kategorien (Normal-, Rand-, Fehlerfall) prüfen jede Funktion gegen von Hand gerechnete Werte, externe Dienste werden durch Attrappen ersetzt, und eine Abweichungsanalyse hält fest, was schiefging und warum.

## Kernidee

- **Testfälle vor Code:** erst Pseudocode, dann rote Tests, dann Implementierung bis grün (Commits wie `test(bm25): … (red until top_m exists)`).
- **Normalfall:** typische Eingabe, Ergebnis von Hand nachgerechnet. **Randfall:** leer, genau eins, Gleichstand, Sonderzeichen, Grenzwerte. **Fehlerfall:** ungültige Eingabe oder ausfallender Dienst, erwartet ein eigener Fehler oder geregelter Ausweichweg.
- **Attrappen:** `FakeFetch`, `FakePost`, `FakeSource`, `TopicEmbedder`; Tests laufen ohne Netz, ohne Schlüssel, immer gleich.
- **Datenbank:** Tests gegen `algorithmusprojekt_test`, jeder in einer zurückgerollten Transaktion; ohne Datenbank werden sie übersprungen (ein Skip ist kein Pass).
- **Coverage:** Zeilen und Verzweigungen (`coverage --branch`).

## Ablauf

```
python -m unittest discover -s src -t src
python -m coverage run --branch -m unittest discover -s src -t src
python -m coverage report --omit="*/test_*,*/__init__.py"
python Phase4/testkatalog.py      # erzeugt Phase4/Testkatalog.md, Kategorie nach Testname
```

## Mini-Beispiel

| Kategorie | Fall | Input → erwartet |
|---|---|---|
| Normal N3 | `bm25.top_m` | „apfel milch“, m = 2 → `[(3, 0.767), (0, 0.694)]` |
| Rand R5 | `cosine_similarity` | Nullvektor (0, 0) und (1, 2) → 0,0 statt Division durch null |
| Fehler F1 | `split_into_chunks` | overlap = 4 bei chunk_size = 4 → `ValueError` |
| Fehler F5 | `research` hybrid | Einbetter wirft → BM25-Ergebnis plus Hinweis (R10) |

## Zahlen (Stand 15.11.2026)

- 325 Tests: 135 Normal-, 125 Rand-, 65 Fehlerfälle; alle wie erwartet. Laufzeit der Suite etwa 1,2 s.
- Coverage gesamt 97 %; `bm25`, `chunking`, `ranking`, `pipeline`, `cache` 100 %; `mcp_server` 82 % (Serverstart über die Kommandozeile nicht getestet).
- Nicht abgedeckt: echte Netzwerkaufrufe (`http_get`, `http_post_json`) und Serverstart, bewusst durch Attrappen ersetzt.

## Abweichungsanalyse (Auswahl)

- 6.1 `insert_chunks.sql`: „function unnest(unknown) is not unique“ → Cast `::text[]`.
- 6.2 BM25 `ZeroDivisionError` bei k1 = 0 und f = 0 → früher Rücksprung mit 0.
- 6.3 Tokenizer klebte „and/or“ zu „andor“ → Satzzeichen werden Leerzeichen.
- 6.4 Schema-Regeln durch einen Merge verloren → `schema.sql` nach jedem Merge zweimal ausführen.
- 6.5 Kein Bug, aber Abweichung vom Entwurf: BM25 filtert auf Abstracts kaum vor (L1).

## Typische Prüferfragen

- **Warum hat `bm25` keinen Fehlerfall?** So entworfen: BM25 wirft nie, sondern liefert bei leerem Index, leerer Anfrage oder m = 0 eine leere Liste (38 Randfälle).
- **Wie testen Sie ohne arXiv und Voyage?** Die Funktionen bekommen `fetch` bzw. `post` übergeben; Tests reichen Attrappen hinein.
- **Beweisen 97 % Coverage, dass das Ranking gut ist?** Nein; Unittests prüfen kleine, ausgedachte Beispiele. Die Qualität zeigen erst die Messläufe.
- **Wie wurden die Kategorien vergeben?** Skript nach Testnamen und `assertRaises`; vier Fälle von Hand umsortiert.

## Stolperfallen

- Ohne laufende Testdatenbank werden Storage-/Cache-Tests übersprungen; dann nicht „alle grün“ behaupten.
- Den Testkatalog nur mit laufender Datenbank neu erzeugen, sonst ändern die Skips ihn.
