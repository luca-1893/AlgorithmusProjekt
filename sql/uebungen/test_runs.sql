-- Testfälle für die Regeln in runs.
-- Eigenständig: braucht keine anderen Tabellen. Jeder Fehlerfall verletzt genau eine Regel.
-- Jeden Insert einzeln ausführen (Cursor hinein, ⌘ + Enter).

-- R1: agent_websearch ohne Schlagwörter und k            erwartet: ✅, found_source = NULL
INSERT INTO runs (run_at, variant, keywords, question, k, input_tokens, output_tokens, duration_ms)
VALUES (now(), 'agent_websearch', NULL, 'Testfrage 1', NULL, 4200, 350, 12000)
RETURNING id, found_source;

-- R2: bm25 mit Schlagwörtern und k = 5                   erwartet: ✅
INSERT INTO runs (run_at, variant, keywords, question, k, input_tokens, output_tokens, duration_ms)
VALUES (now(), 'bm25', '{semantics,uml}', 'Testfrage 1', 5, 1800, 300, 900);

-- R3: hybrid mit k = 20 (Obergrenze)                     erwartet: ✅
INSERT INTO runs (run_at, variant, keywords, question, k, input_tokens, output_tokens, duration_ms)
VALUES (now(), 'hybrid', '{semantics,uml}', 'Testfrage 1', 20, 2100, 320, 2500);

-- R4: k = 1 (Untergrenze), 0 Tokens und 0 ms             erwartet: ✅
INSERT INTO runs (run_at, variant, keywords, question, k, input_tokens, output_tokens, duration_ms)
VALUES (now(), 'bm25', '{uml}', 'Testfrage 2', 1, 0, 0, 0);

-- R5: unbekannte Variante (Großschreibung)               erwartet: 23514 runs_invalid_variant
INSERT INTO runs (run_at, variant, keywords, question, k, input_tokens, output_tokens, duration_ms)
VALUES (now(), 'BM25', '{uml}', 'Testfrage 2', 5, 100, 10, 10);

-- R6: bm25 ohne Schlagwörter                             erwartet: 23514 runs_invalid_keywords
INSERT INTO runs (run_at, variant, keywords, question, k, input_tokens, output_tokens, duration_ms)
VALUES (now(), 'bm25', NULL, 'Testfrage 2', 5, 100, 10, 10);

-- R7: agent_websearch mit Schlagwörtern                  erwartet: 23514 runs_invalid_keywords
INSERT INTO runs (run_at, variant, keywords, question, k, input_tokens, output_tokens, duration_ms)
VALUES (now(), 'agent_websearch', '{uml}', 'Testfrage 2', NULL, 100, 10, 10);

-- R8: hybrid ohne k                                      erwartet: 23514 runs_k_null
INSERT INTO runs (run_at, variant, keywords, question, k, input_tokens, output_tokens, duration_ms)
VALUES (now(), 'hybrid', '{uml}', 'Testfrage 2', NULL, 100, 10, 10);

-- R9: agent_websearch mit k                              erwartet: 23514 runs_k_null
INSERT INTO runs (run_at, variant, keywords, question, k, input_tokens, output_tokens, duration_ms)
VALUES (now(), 'agent_websearch', NULL, 'Testfrage 2', 5, 100, 10, 10);

-- R10: k = 0                                             erwartet: 23514 runs_invalid_k
INSERT INTO runs (run_at, variant, keywords, question, k, input_tokens, output_tokens, duration_ms)
VALUES (now(), 'bm25', '{uml}', 'Testfrage 2', 0, 100, 10, 10);

-- R11: k = 21                                            erwartet: 23514 runs_invalid_k
INSERT INTO runs (run_at, variant, keywords, question, k, input_tokens, output_tokens, duration_ms)
VALUES (now(), 'bm25', '{uml}', 'Testfrage 2', 21, 100, 10, 10);

-- R12: negative Input-Tokens                             erwartet: 23514 runs_invalid_input_tokens
INSERT INTO runs (run_at, variant, keywords, question, k, input_tokens, output_tokens, duration_ms)
VALUES (now(), 'bm25', '{uml}', 'Testfrage 2', 5, -1, 10, 10);

-- R13: negative Output-Tokens                            erwartet: 23514 runs_invalid_output_tokens
INSERT INTO runs (run_at, variant, keywords, question, k, input_tokens, output_tokens, duration_ms)
VALUES (now(), 'bm25', '{uml}', 'Testfrage 2', 5, 100, -1, 10);

-- R14: negative Dauer                                    erwartet: 23514 runs_invalid_duration_ms
INSERT INTO runs (run_at, variant, keywords, question, k, input_tokens, output_tokens, duration_ms)
VALUES (now(), 'bm25', '{uml}', 'Testfrage 2', 5, 100, 10, -1);

-- R15: Startzeitpunkt fehlt                              erwartet: 23502 (not-null run_at; kein DEFAULT, E25)
INSERT INTO runs (variant, keywords, question, k, input_tokens, output_tokens, duration_ms)
VALUES ('bm25', '{uml}', 'Testfrage 2', 5, 100, 10, 10);

-- R16: Frage fehlt                                       erwartet: 23502 (not-null question)
INSERT INTO runs (run_at, variant, keywords, question, k, input_tokens, output_tokens, duration_ms)
VALUES (now(), 'bm25', '{uml}', NULL, 5, 100, 10, 10);

-- R17: Lauf nachträglich bewerten                        erwartet: ✅, 1 Zeile geändert
UPDATE runs SET found_source = true WHERE variant = 'hybrid' AND question = 'Testfrage 1';

-- Stand: erwartet 4 Läufe (R1 bis R4), davon einer bewertet
SELECT id, variant, keywords, k, found_source FROM runs ORDER BY id;

-- Aufräumen
DELETE FROM runs;
