# Messfragen: Entwurf

Vorschlag für die 25 Messfragen aus `testfragen.md` (Kriterien „Wann eine Frage taugt“, Feldformat wie dort). Die Fragen sollen die Leitfragen L1–L6 aus `leitfragen.md` auswertbar machen, insbesondere L5 (deutsch gegen englisch) und L6 (Volltext gegen Abstract).

**Stand:** 15.11.2026
**Status:** Entwurf, Auswahl durch Luca. Noch nicht in `testfragen.md` übernommen.

## Vorgehen bei der Prüfung

- **arXiv-API:** Jede ID wurde über `http://export.arxiv.org/api/query?id_list=…` abgefragt (mindestens 3 s Pause zwischen den Anfragen). Titel, Erstautor, Primärkategorie und Abstract passen zur Frage.
- **Abstract-Fragen:** Die Referenzantwort steht wörtlich im Abstract der API (per Textsuche bestätigt).
- **Volltext-Fragen:** Volltext über `https://arxiv.org/html/<id>` (jeweils neueste Version, siehe Spalte „geprüft“) gelesen. Die Referenzantwort steht im genannten Abschnitt und per Textsuche **nicht** im Abstract.
- **Doppelungen:** Für jede ID eine Titelsuche über die API (`ti:`-Suche mit den ersten Titelwörtern) und, wo sinnvoll, eine Suche nach dem Namen des Verfahrens oder Datensatzes. Kein zweiter arXiv-Eintrag mit gleichem Titel oder gleicher DOI gefunden. Verwandte Arbeiten derselben Gruppen stehen unter „Risiken“.
- **Nicht geprüft:** Ob ein Sprachmodell die Antwort ohne Recherche kennt. Um das Risiko klein zu halten, stammen 22 von 25 Paper aus 2025 und 2026; F02 und F17 sind von 2024, F03 von 2023.

## Messfragen

F01–F13: Fundstelle im Volltext. F14–F25: Fundstelle im Abstract.

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

## Mischung

| Merkmal | Anzahl |
|---|---|
| deutsch / englisch | 13 / 12 |
| Fundstelle Volltext / Abstract | 13 / 12 |
| Volltext deutsch / englisch | 7 / 6 |
| Abstract deutsch / englisch | 6 / 6 |
| arXiv-Hauptkategorien | 11: cs (11 Fragen), physics (4), astro-ph (2), eess, quant-ph, econ, q-bio, q-fin, cond-mat, math, gr-qc (je 1) |
| Erscheinungsjahr | 2023: 1, 2024: 2, 2025: 12, 2026: 10 |

Bezug zu den acht Anfragen aus `messungen/2026-10-19_review-pr24/`: UML (F13, F14), BM25 (F21), RAG und Halluzination (F12), GNN und Moleküle (F10), RL und Robotik/Sim-to-Real (F01), Quantenfehlerkorrektur (F03), föderiertes Lernen und Differential Privacy (F02). Transformer/Attention fehlt als eigenes Thema; Cross-Attention kommt nur in F18 vor.

Für L5 ist die Sprache je Frage festgelegt; für L6 sind Volltext- und Abstract-Fragen nach Nummern getrennt (F01–F13 / F14–F25).

## Risiken pro Frage

| Nr. | Risiko |
|---|---|
| F01 | Länge ist als „exceeding 1.8 meters“ angegeben, also nur Untergrenze; Antwort „über 1,8 m“ gilt. |
| F02 | Parameterzahl ist sehr spezifisch; Antworten mit gerundeter Zahl („ca. 8,9 Mio.“) vorher als richtig oder falsch festlegen. |
| F03 | Ältestes Paper (2023) und in der QEC-Community bekannt; Modell könnte es kennen. Die Architektur folgt einem früheren Paper (Baireuther et al., Ref. [64]); ob dort dieselben Zustandsgrößen stehen, ist ungeprüft. |
| F04 | Es gibt mehrere AIFS-Folgepaper (AIFS-SUBS 2607.05100, AIFS-COMPO 2604.03300). In AIFS-SUBS kommt HardTanh nicht vor (geprüft), AIFS-COMPO ist ungeprüft. Laut 2509.18994 nutzte das prä-operationelle AIFS noch Clipping statt HardTanh; das Original-AIFS-Paper (2406.01465) ist nicht gelesen. |
| F05 | Zwei Fakten in zwei Abschnitten; als Referenz zählt nur das Modell. „GPT-4o“ ohne Version vorher als richtig oder falsch festlegen. |
| F06 | Verwechslungsgefahr mit dem Testset (100 E-Mails) und mit 947 Technik-Beispielen im Trainingsset. |
| F07 | Dieselbe Gruppe hat ein ähnliches Paper (2602.19829, Dual-Domain-Netz für tragbares MRT) mit anderer Architektur; Verwechslung möglich. |
| F08 | Vier Teile in der Antwort; Teiltreffer müssen vorher geregelt werden. JOB und Stack sind auch aus anderen Learned-Optimizer-Papern (Bao) bekannt. |
| F09 | Frage verrät, dass es eine kleinere Schrittzahl gab; die Zahl 200 nicht. |
| F10 | Dataset-Paper derselben Gruppe (2404.16196) enthält WL-OA nicht (geprüft). Folgepaper 2509.18703 (Graph-ML für Pestizide) ist ungeprüft und könnte ähnliche Ergebnisse berichten. |
| F11 | Die Anlage kommt vermutlich auch in anderen Arbeiten derselben Gruppe vor (ungeprüft); die Anlage allein ist daher eher erratbar als die 170 bar. |
| F12 | „Über 180.000“ ist eine Untergrenze; genaue Zahl steht nicht im Text. |
| F13 | Uneinheitliche Modellbezeichnung im Paper (GPT-4 / GPT-4o). |
| F14 | Titel enthält „Class and Activity Diagrams“; Frage umschreibt das, ist aber nah dran. |
| F15 | Die drei Dialektgruppen sind allgemein bekannt; ein Modell könnte sie für Südostdeutschland raten, ohne das Paper zu kennen. Dann zählt nur `found_source`. |
| F16 | Zu WASP-80 b gibt es vermutlich weitere JWST-Paper (ungeprüft); der CS₂-Nachweis mit 6,3 σ ist spezifisch für dieses Paper. |
| F17 | Mehrere Paper zum deutschen Mindestlohn (z. B. 2310.15964, 2111.13692); die Elastizität −0,1 für Minijobs ist spezifisch für 2403.17206. |
| F18 | R²-Werte für k_cat und K_m liegen nah beieinander (0,593 / 0,607); Vertauschen möglich. |
| F19 | Abstract enthält viele Zahlen (t = 3,63; MSFE 0,959 für Ethereum); Verwechslung möglich. |
| F20 | Zu La3Ni2O7 unter Druck gibt es viele Paper mit abweichenden Übergangsdrücken; die Antwort „nahe 10 GPa“ gilt nur für dieses Paper (Einkristall, Helium). Hohe Gefahr, dass eine andere Quelle zitiert wird. |
| F21 | Zahlen sehr spezifisch, Risiko gering. |
| F22 | Kissat wird in mehreren Ramsey-Arbeiten genutzt, auch in einem Folgepaper derselben Autoren (2607.06817, reflektive und diedrische Ramsey-Zahlen, ungeprüft). Antwort evtl. auch in einem Folgepaper. |
| F23 | Frage umschreibt TESS; „Nearby Young Moving Groups“ steht im Titel und wird nicht genannt. |
| F24 | Pulsdauer und Bandbreite stehen nah beieinander; Risiko gering. |
| F25 | Ähnliche Studie derselben Gruppe zu Spins (2510.05029) behandelt Glitches ebenfalls; Grenzwert SNR 50 steht im Abstract von 2506.21869. |

Allgemein: Abstract-Fragen mit sehr spezifischen Begriffen (WASP-80 b, KXRECSSNBER, Kissat) sind für BM25 leicht, weil seltene Begriffe eine hohe IDF haben. Wenn die Abstract-Fragen gleichmäßig schwer sein sollen, lassen sich diese Begriffe aus der Frage nehmen.

## Ersatzfragen

| Nr. | Frage | Sprache | erwartete Quelle | Fundstelle | Referenzantwort | Anmerkung | Fachgebiet | geprüft |
|---|---|---|---|---|---|---|---|---|
| R1 | In the 2026 lab on scientific retrieval under collection change, which family of runs obtained the best ARP on all three snapshots, and with which nDCG@10 values? | en | 2607.04088 | Abstract | zeitlich gewichteter Volltext-BM25 (FT BM25+temporal und +citation); 0,285 / 0,267 / 0,180 | passt zum Projektthema (Volltext gegen Titel+Abstract) | cs.IR | ja (API) |
| R2 | Wie viele Klassen von Störsignalen fand ein Variational Autoencoder mit Spektralclustering in den O3GK-Daten des japanischen Gravitationswellendetektors? | de | 2510.14291 | Abstract | acht | „O3GK“ steht auch im Titel | gr-qc | ja (API) |
| R3 | How many neurons are covered by the light-sheet recordings behind a 2025 benchmark for forecasting cellular-resolution activity across an entire larval fish brain? | en | 2503.02618 | Abstract | über 70.000 | Begleitpaper 2503.00073 nutzt denselben Datensatz; dort evtl. gleiche Zahl | q-bio.NC | ja (API) |
| R4 | Eine Studie zur Ladeflexibilität öffentlicher E-Auto-Ladepunkte in Prag nutzt Sitzungsdaten eines Verteilnetzbetreibers und Ungleichgewichtsdaten eines Übertragungsnetzbetreibers. Welche beiden Unternehmen sind das? | de | 2608.18126 | Volltext, Abschnitt 3.1 „Data and Approach“ | PREdistribuce, a.s. (Ladedaten) und ČEPS (Systemungleichgewicht) | Volltext-Ersatz | math.OC | ja (API; Volltext HTML v1) |

## Offen für die Auswahl

- Bewertung von Teiltreffern (F05, F08, F11) und gerundeten Zahlen (F02, F12) vor der Messung festlegen, nicht danach.
- Alle Volltext-Stellen stammen aus der jeweils neuesten HTML-Version (in der Spalte „geprüft“ vermerkt). Kommt später eine neue Version, kann sich die Stelle verschieben.
- Ob ein Modell einzelne Fragen ohne Recherche beantworten kann, ist nicht geprüft; das zeigt erst ein Vorlauf mit `agent_websearch` oder ein Lauf ohne Werkzeuge.
