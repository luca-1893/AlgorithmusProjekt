-- Testfälle für die Regeln in chunks.
-- Voraussetzung: die Dokumente aus test_documents.sql (Fall 1, 3 und 8) stehen in documents.
-- Die IDs werden über source und source_id nachgeschlagen, damit Lücken in den IDs keine Rolle spielen.
-- Jeden Insert einzeln ausführen (Cursor hinein, ⌘ + Enter) und vorher die Vorhersage prüfen.

-- Vorbereitung: Welche Dokumente gibt es?
SELECT id, source, source_id FROM documents ORDER BY id;

-- T1: gültiger Chunk, position 0                      erwartet: ✅
INSERT INTO chunks (document_id, position, text)
VALUES ((SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '1409.6928'), 0, 'Erster Abschnitt A');

-- T2: zweiter Chunk desselben Dokuments, position 1    erwartet: ✅
INSERT INTO chunks (document_id, position, text)
VALUES ((SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '1409.6928'), 1, 'Zweiter Abschnitt A');

-- T3: position 0 für ein anderes Dokument              erwartet: ✅
INSERT INTO chunks (document_id, position, text)
VALUES ((SELECT id FROM documents WHERE source = 'semantic_scholar' AND source_id = '1409.6928'), 0, 'Erster Abschnitt B');

-- T4: gleiches Dokument und gleiche position nochmal   erwartet: 23505 chunks_primary_key
INSERT INTO chunks (document_id, position, text)
VALUES ((SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '1409.6928'), 0, 'Doppelt');

-- T5: position -1                                      erwartet: 23514 chunks_invalid_position
INSERT INTO chunks (document_id, position, text)
VALUES ((SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '1409.6928'), -1, 'Negativ');

-- T6: Dokument, das es nicht gibt                      erwartet: 23503 chunks_document_foreign_key
INSERT INTO chunks (document_id, position, text)
VALUES (999999, 0, 'Ohne Dokument');

-- T7: document_id fehlt                                erwartet: 23502 (not-null)
INSERT INTO chunks (document_id, position, text)
VALUES (NULL, 0, 'Ohne document_id');

-- T8: position fehlt                                   erwartet: 23502 (not-null)
INSERT INTO chunks (document_id, position, text)
VALUES ((SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '1409.6928'), NULL, 'Ohne Position');

-- T9: text fehlt                                       erwartet: 23502 (not-null)
INSERT INTO chunks (document_id, position, text)
VALUES ((SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '1409.6928'), 2, NULL);

-- T10: leerer Text                                     erwartet: 23514 chunks_invalid_text
INSERT INTO chunks (document_id, position, text)
VALUES ((SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '1409.6928'), 2, '');

-- Stand vor T11: erwartet 3 Zeilen (T1, T2, T3)
SELECT document_id, position, text FROM chunks ORDER BY document_id, position;

-- T11: Dokument mit Chunks löschen                      erwartet: seine Chunks verschwinden mit (CASCADE)
-- 11a: Chunks für das Dokument aus Fall 8 anlegen
INSERT INTO chunks (document_id, position, text)
VALUES ((SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '2001.00008'), 0, 'Abschnitt G0'),
       ((SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '2001.00008'), 1, 'Abschnitt G1');

-- 11b: Wie viele Chunks hat das Dokument?             erwartet: 2
SELECT count(*) FROM chunks
WHERE document_id = (SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '2001.00008');

-- 11c: Dokument löschen
DELETE FROM documents WHERE source = 'arxiv' AND source_id = '2001.00008';

-- 11d: Stand danach: erwartet wieder 3 Zeilen, keine Chunks mehr zu Abschnitt G
SELECT document_id, position, text FROM chunks ORDER BY document_id, position;

-- Aufräumen, wenn fertig (Fall 8 aus test_documents.sql ist durch T11 schon gelöscht):
-- DELETE FROM chunks;
