# Testfragen für die Messläufe

Grundlage für die KPI-Messung (Karte #6 und #7): Jede Frage wird mit allen drei Varianten beantwortet, und jeder Lauf landet als Zeile in `runs` (siehe `docs/storage/schema-entwurf.md`).

| Variante | Was passiert |
|---|---|
| `agent_websearch` | Der Agent bekommt nur die Frage und recherchiert mit seiner eingebauten Websuche, ohne `research_papers`. |
| `bm25` | Der Agent nutzt `research_papers`, die Pipeline läuft ohne Einbetter. |
| `hybrid` | Der Agent nutzt `research_papers` mit Voyage (BM25, Vektorsuche, RRF, MMR). |

## Wann eine Frage taugt

1. **Eine eindeutige Quelle:** Die Antwort steht in genau einem arXiv-Paper, dessen ID wir kennen. „Richtige Quelle gefunden“ heißt: Diese arXiv-ID steht unter den Quellen der Antwort.
2. **Nachprüfbar:** Die Stelle ist notiert (Abstract oder Abschnitt im Volltext), dazu eine kurze Referenzantwort.
3. **Nicht aus dem Gedächtnis beantwortbar:** Lieber weniger bekannte Paper. Bei Klassikern wie „Attention Is All You Need“ antwortet ein Modell ohne Recherche, und die Messung zeigt dann nichts.
4. **Titel nicht abschreiben:** Die Frage soll das Thema beschreiben, nicht die Wörter des Titels wiederholen, sonst ist die Suche trivial.
5. **Mischung:**
   - etwa die Hälfte mit Antwort nur im **Volltext**, nicht im Abstract (das prüft den Volltext-Weg)
   - deutsche und englische Fragen (Abstracts sind englisch)
   - verschiedene Fachgebiete, z. B. die acht Anfragen aus `messungen/2026-10-19_review-pr24/`
6. **Umfang:** 25 Fragen (Luca, 15.11.2026). Weniger ergibt keine belastbare Trefferquote, mehr kostet zu viele Tokens.

## Was der Mess-Agent pro Lauf liefern muss

Damit ein Lauf in `runs` gespeichert werden kann (`insert_run.sql`):

| Spalte | Woher |
|---|---|
| `run_at` | Startzeitpunkt beim Senden des Prompts (von Python) |
| `variant` | `agent_websearch`, `bm25` oder `hybrid` |
| `keywords` | die Schlagwörter, mit denen der Agent `research_papers` aufgerufen hat; bei `agent_websearch` leer (`NULL`) |
| `question` | die Frage aus dieser Liste, wörtlich |
| `k` | das `k` des Tool-Aufrufs; bei `agent_websearch` leer (`NULL`) |
| `input_tokens`, `output_tokens` | exakte Werte aus der API-Antwort, über alle Schritte des Agenten summiert |
| `duration_ms` | vom Senden des Prompts bis zur fertigen Antwort |
| `found_source` | automatisch nach jedem Lauf: wahr, wenn die erwartete arXiv-ID in der Antwort steht (`evaluation.messlauf.found_source`); Stichprobe von Hand über das Log |

Gleiches Modell und gleicher System-Prompt für alle drei Varianten, sonst sind die Zahlen nicht vergleichbar. Umgesetzt in `src/evaluation/messlauf.py` (Aufruf siehe README, Abschnitt „Messläufe“; Prüfung von Hand: `Phase4/Klicktest-runs.md`).

## Fragen

Felder: **Nr.**, **Frage**, **Sprache**, **erwartete Quelle** (arXiv-ID ohne Version), **Fundstelle**, **Referenzantwort**, **Anmerkung**.

### Format-Beispiele

Die drei Beispiele sind gegen die arXiv-API geprüft (Titel, ID, Abstract). Die ersten beiden verletzen absichtlich Kriterium 3 und zeigen nur das Format; für die Messung durch weniger bekannte Paper ersetzen.

| Nr. | Frage | Sprache | erwartete Quelle | Fundstelle | Referenzantwort | Anmerkung |
|---|---|---|---|---|---|---|
| B1 | Welchen BLEU-Wert erreichte die erste rein aufmerksamkeitsbasierte Übersetzungsarchitektur auf der WMT-2014-Aufgabe Englisch–Deutsch? | de | 1706.03762 | Abstract | 28,4 BLEU | zu bekannt (Kriterium 3) |
| B2 | Which two kinds of memory does retrieval-augmented generation combine for knowledge-intensive tasks? | en | 2005.11401 | Abstract | parametrisch (vortrainiertes seq2seq-Modell) und nicht-parametrisch (dichter Vektorindex über Wikipedia) | zu bekannt (Kriterium 3) |
| B3 | Welche Arbeitsgruppe arbeitete Ende der 1990er an einer präzisen Semantik für UML-Klassendiagramme? | de | 1409.6928 | Abstract | die Precise UML Group (PUML) | Achtung: 1409.6919 trägt dieselbe DOI; als Treffer zählen, wenn beide gelten sollen, vorher festlegen |

### Messfragen

Übernommen aus `messfragen-entwurf.md` (Luca, 15.11.2026: alle 25, keine Ersatzfrage). Dort stehen auch die Prüfung jeder Frage, die Risiken pro Frage und die Ersatzfragen R1–R4. F01–F13: Fundstelle im Volltext, F14–F25: im Abstract.

| Nr. | Frage | Sprache | erwartete Quelle | Fundstelle | Referenzantwort | Anmerkung | Fachgebiet | geprüft |
|---|---|---|---|---|---|---|---|---|
| F01 | Ein über 300 kg schwerer, ölgetriebener Laufroboter mit vier Beinen hat das Gehen in der Simulation per Reinforcement Learning gelernt. Welche zusätzliche Fortbewegungsart besitzt die Plattform, und wie lang ist sie? | de | 2601.11143 | Volltext, Abschnitt III-A „Hydraulic quadruped robot“ | zwei Räder mit Differentialantrieb (Fahren und Laufen); Länge über 1,8 m | Abstract nennt nur über 300 kg und 12 Aktuatoren. DOI 10.1109/LRA.2025.3623024 | cs.RO | ja (API; Volltext HTML v1) |
| F02 | A study trained a multi-label ECG classifier on about 1.5 million tracings from seven Canadian hospitals without pooling the raw data. How many parameters does its residual convolutional network have? | en | 2405.00725 | Volltext, Abschnitt 3.3 „Learning Algorithm“ | 8.922.644 Parameter | Abstract nennt 1.565.849 EKGs und 7 Krankenhäuser, nicht die Parameterzahl | eess.SP | ja (API; Volltext HTML v2) |
| F03 | Ein rekurrentes neuronales Netz dekodiert Syndromdaten kleiner topologischer Codes, unter anderem aus Googles Transmon-Experiment von 2023. Wie groß sind die internen Zustände der beiden LSTM-Schichten bei Codedistanz 7? | de | 2307.03280 | Volltext, Abschnitt II.3 „Neural network architecture“ | N_L = 128 (64 / 96 / 128 für d = 3 / 5 / 7) | LSTM kommt im Abstract nicht vor. DOI 10.1103/PhysRevResearch.7.013029 | quant-ph | ja (API; Volltext HTML v2) |
| F04 | In the 2025 revision of a European weather centre's machine-learned forecast model, which activation function ensures that predicted convective precipitation never exceeds total precipitation? | en | 2509.18994 | Volltext, Abschnitt 3.2 „Bounding the Outputs with Activation Functions“, Gl. (2) | HardTanh: cp = HardTanh(cp′) · tp („FractionBounding“) | Abstract nennt nur „bounding layers“ | physics.ao-ph | ja (API; Volltext HTML v1) |
| F05 | In einer Online-Studie mit 130 Personen wurden technische Alarme eines Einbruchserkennungssystems für vernetzte Haushalte von einem Sprachmodell in verständliche Hinweise übersetzt. Welches Modell in welcher Version hat die Hinweise erzeugt? | de | 2510.21508 | Volltext, Abschnitt 3.3 „Generation of Security Notifications“, Unterabschnitt „LLM Setup“ | GPT-4o, Version 2024-05-13, über die OpenAI-API | Zusatzfakt (Abschnitt 4.1): Rekrutierung über Prolific, 2,50 £ pro Person. DOI 10.1007/978-3-032-07989-3_19 | cs.HC | ja (API; Volltext HTML v1) |
| F06 | A study used few-shot prompting to label the psychological manipulation techniques in French phishing emails. How many real emails from 2023 were in its training set, and how many synthetic emails were added? | en | 2506.22515 | Volltext, Abschnitt 4.2 „Dataset“ | 284 echte E-Mails (SignalSpam, 2023) und 81 synthetische | Abstract nennt nur das Testset (100 E-Mails); naheliegende Verwechslung | cs.CR | ja (API; Volltext HTML v1) |
| F07 | Ein Deep-Learning-Verfahren mit Nesterov-Momentum verbessert Aufnahmen eines mobilen Niederfeld-MRT mit 47 mT und Halbach-Magnet. Aus wie vielen kaskadierten Blöcken besteht das Netz? | de | 2509.11790 | Volltext, Abschnitt II-B „Implementation Details“ | fünf Iterationsblöcke (je Datenkonsistenz, Residualverbindung und ein CNN aus sieben ResNet-Blöcken) | Abstract nennt 47 mT, nicht die Blockzahl | physics.med-ph | ja (API; Volltext HTML v1) |
| F08 | An offline optimizer for repeatedly executed analytical SQL queries combines a variational autoencoder with Bayesian search over execution plans. On which four benchmark workloads was it evaluated? | en | 2502.05256 | Volltext, Abschnitt 5.1 „Setup“ | JOB, CEB (Teilmenge), Stack (Teilmenge), DSB | Abstract sagt nur „several datasets“. Antwort aus vier Teilen: Bewertung vorher festlegen (alle vier nötig?) | cs.DB | ja (API; Volltext HTML v1) |
| F09 | Ein Verfahren behandelt US-Grippesaisons als Bilder (Zeit mal Ort) und erstellt Prognosen per Inpainting mit einem Diffusionsmodell. Mit wie vielen Entrauschungsschritten wurden die Prognosen besser als mit der kleineren getesteten Schrittzahl? | de | 2604.24913 | Volltext, Abschnitt 3.3 „Training data mix and model formulation determine forecast skill“ | 500 statt 200 Schritte (dazu Wurzel-Skalierung) | Abstract nennt nur die Datenmischung 30 % / 70 %. DOI 10.1371/journal.pcbi.1014846 | cs.LG | ja (API; Volltext HTML v2) |
| F10 | In a benchmark of fingerprints, graph kernels and graph neural networks for predicting which agrochemicals harm Apis mellifera, which method achieved the highest MCC and AUROC on the MaxMin split? | en | 2503.24305 | Volltext, Abschnitt 4 „Results and discussion“, Tabelle 1 | WL-OA-Graphkern (Weisfeiler-Lehman Optimal Assignment) | Abstract nennt keine Gewinnermethode | cs.LG | ja (API; Volltext HTML v4) |
| F11 | Bei Windkanalversuchen mit Druckluft wurde die Drehzahl eines Modellrotors periodisch moduliert, um wandernde Störungen im Nachlauf bei Re_D = 4·10^6 zu untersuchen. In welcher Anlage fanden die Versuche statt, und bis zu welchem statischen Druck? | de | 2505.22788 | Volltext, Abschnitt III.1 „Experimental apparatus“ | High Reynolds number Test Facility (HRTF) der Princeton University; bis 170 bar | Abstract nennt nur „pressurized-air wind tunnel“. DOI 10.1103/18jm-6bzj | physics.flu-dyn | ja (API; Volltext HTML v2) |
| F12 | A biomedical RAG framework uses Negative Knowledge Assertions and preference optimization to penalize hallucinated answers. How many QA pairs does the dataset contain that the authors build by merging the MedQA and MedMCQA training sets? | en | 2510.14400 | Volltext, Abschnitt II-C1 „MedRankQA Dataset Construction“ | über 180.000 QA-Paare (MedRankQA) | Datensatzname und Zahl nicht im Abstract | cs.CL | ja (API; Volltext HTML v2) |
| F13 | Ein Verbund spezialisierter Sprachmodell-Agenten (Entitäten extrahieren, Beziehungen klassifizieren, Diagramm zusammensetzen) wurde in der Northwind-Fallstudie mit direktem Prompting von GPT-4o verglichen. Wie veränderte sich der strikte F1-Wert bei den Beziehungen? | de | 2511.22409 | Volltext, Abschnitt V-A2 „Depth Evaluation“, Tabelle III | von 0,52 auf 0,92 | Northwind steht im Abstract, die F1-Werte nicht. Der Text schreibt an dieser Stelle „GPT-4“, Tabelle und Setup „GPT-4o“. DOI 10.5220/0014301900004058 | cs.SE | ja (API; Volltext HTML v2) |
| F14 | Ein öffentlicher Datensatz verknüpft per Hand gezeichnete Skizzen von Softwaremodellen mit geprüftem, renderbarem Diagrammcode. Wie viele der Skizzen zeigen statische Strukturmodelle und wie viele Abläufe? | de | 2608.07036 | Abstract | 271 Klassendiagramme und 286 Aktivitätsdiagramme (557 insgesamt) | | cs.SE | ja (API) |
| F15 | An evaluation set from Interspeech 2025 contains about four hours of read speech from Southeast Germany plus half an hour of standard-language speech. Which three regional varieties does it cover? | en | 2506.02894 | Abstract | Fränkisch, Bairisch, Alemannisch (Franconian, Bavarian, Alemannic) | englische Frage zu deutschem Thema. DOI 10.21437/Interspeech.2025-318 | cs.CL | ja (API) |
| F16 | Welches schwefelhaltige Molekül wurde mit NIRCam und MIRI im Transmissionsspektrum des warmen Gasriesen WASP-80 b eindeutig nachgewiesen, und mit welcher Signifikanz? | de | 2604.13168 | Abstract | CS₂ (Kohlenstoffdisulfid), 6,3 σ (ln B = 17,89) | | astro-ph.EP | ja (API, Version v3) |
| F17 | Using the German Structure of Earnings Survey for 2010, 2014 and 2018, what wage elasticity of employment did researchers derive for marginal low-pay jobs after the national wage floor of 2015? | en | 2403.17206 | Abstract | −0,1 (für Minijobs) | | econ.GN | ja (API) |
| F18 | Ein CLIP-artiges Modell kombiniert ESM-2- und ChemBERTa-Einbettungen, um katalytische Wechselzahlen und Michaelis-Konstanten vorherzusagen. Welches R² erreicht es für k_cat? | de | 2512.00379 | Abstract | R² = 0,593 (für K_m 0,607); Trainingsdaten CatPred-DB | | q-bio.BM | ja (API) |
| F19 | Event-contract probabilities from a regulated US prediction exchange were used to predict how turbulent Bitcoin prices become. Which recession-related contract series was the most stable out-of-sample signal, and what MSFE ratio did it achieve? | en | 2604.01431 | Abstract | KXRECSSNBER; MSFE-Verhältnis 0,979 (Clark-West p = 0,020) | | q-fin.ST | ja (API) |
| F20 | Ab welchem Druck wechselt La3Ni2O7, das unter Kompression supraleitend wird, aus der polaren orthorhombischen in die tetragonale Kristallstruktur, wenn Helium als Druckmedium dient? | de | 2607.27607 | Abstract | nahe 10 GPa (Am2m → I4/mmm, zugleich Einsetzen der Volumensupraleitung) | Volltext als HTML nicht verfügbar (404); für Abstract-Frage nicht nötig | cond-mat.supr-con | ja (API) |
| F21 | A method copies the terms that a cross-encoder treats as decisive in semantic search results into the BM25 query. How much does it raise Recall@100 on Natural Questions? | en | 2608.00452 | Abstract | von 0,32 auf 0,47 | passt zum Projektthema BM25 | cs.IR | ja (API) |
| F22 | Welcher SAT-Solver wurde 2026 eingesetzt, um neue kleine Zwei-Farben-Ramsey-Zahlen für Graphen mit vorgegebener Knotenreihenfolge und für eine zyklische Abschwächung davon zu berechnen? | de | 2604.16188 | Abstract | Kissat | | math.CO | ja (API) |
| F23 | Studying stellar eruptions on 417 stars aged 10–150 Myr with NASA's planet-hunting survey satellite, how many times more events were detected at 10-minute cadence than at 30-minute cadence? | en | 2602.20402 | Abstract | 5,5-mal so viele | insgesamt 6.288 Flares aus 27.416 Kandidaten. DOI 10.3847/1538-4357/ae44f2 | astro-ph.SR | ja (API) |
| F24 | Eine Kombination aus Dünnschicht-Lithiumniobat-Modulatoren und einem nichtlinearen Schleifenspiegel aus AlGaAs-on-Insulator erzeugt ultrakurze Lichtpulse. Welche Pulsdauer wurde erreicht? | de | 2608.04931 | Abstract | 55 fs (10-dB-Bandbreite über 90 nm, Wiederholrate 10–20 GHz) | | physics.optics | ja (API) |
| F25 | Below which signal-to-noise ratio can non-Gaussian detector noise lying outside the prior time-frequency region of a gravitational-wave signal be left unmitigated without biasing parameter estimates? | en | 2506.21869 | Abstract | SNR unter 50 (konservativ) | DOI 10.1103/kxbb-dpwp | gr-qc | ja (API) |

### Mischung

| | Volltext | Abstract |
|---|---|---|
| deutsch | 7 | 6 |
| englisch | 6 | 6 |

Dazu 11 arXiv-Hauptkategorien und die Jahrgänge 2023 (1), 2024 (2), 2025 (12), 2026 (10); Details in `messfragen-entwurf.md`, Abschnitt „Mischung“.

### Vor der Messung festlegen

- Wie Teiltreffer (F05, F08, F11) und gerundete Zahlen (F02, F12) bewertet werden. Die Regel muss feststehen, bevor die erste Antwort bewertet wird.

## Auswahl für den Pitch

| Feld | Frage | Warum diese |
|---|---|---|
| deutsch · Volltext | F01 (Laufroboter mit Rädern) | anschaulich, jeder versteht es |
| englisch · Volltext | F06 (Phishing-Mails) | zeigt die Verwechslungsgefahr mit dem Abstract (Testset 100 gegen Trainingsset 284) |
| deutsch · Abstract | F14 (UML-Skizzen) | passt zu den Projektthemen (UML) |
| englisch · Abstract | F21 (BM25, Recall@100) | direkter Bezug zum Projekt |

- Eine Folie „Mischung“ mit der Tabelle oben, den Jahrgängen und den Fachgebieten; damit sind alle 25 abgedeckt, ohne sie einzeln zu zeigen.
- Optional ein Risiko-Beispiel: F20 (viele Paper mit anderen Übergangsdrücken) oder der IDF-Hinweis (WASP-80 b ist für BM25 zu leicht). Das zeigt, dass die Fragen kritisch geprüft wurden.
- Alle 25 in den Anhang oder die Backup-Folien.
