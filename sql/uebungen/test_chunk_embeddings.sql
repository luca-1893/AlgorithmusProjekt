-- Testfälle für die Regeln in chunk_embeddings.
-- Voraussetzung: die Chunks aus test_chunks.sql (T1 bis T3) stehen in chunks:
--   arxiv/1409.6928 mit position 0 und 1, semantic_scholar/1409.6928 mit position 0.
-- Die Dokument-IDs werden über source und source_id nachgeschlagen.
-- Jeden Insert einzeln ausführen (Cursor hinein, ⌘ + Enter).

-- Vorbereitung: Welche Chunks gibt es?
SELECT c.document_id, d.source, d.source_id, c.position
FROM chunks c
JOIN documents d ON d.id = c.document_id
ORDER BY c.document_id, c.position;

-- E1: gültiger Vektor                                   erwartet: ✅
INSERT INTO chunk_embeddings (document_id, position, model, embedding)
VALUES ((SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '1409.6928'), 0,
        'voyage-4', ARRAY[0.1, 0.2, 0.3]);

-- E2: gleicher Chunk, anderes Modell                    erwartet: ✅
INSERT INTO chunk_embeddings (document_id, position, model, embedding)
VALUES ((SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '1409.6928'), 0,
        'voyage-4-lite', ARRAY[0.4, 0.5, 0.6]);

-- E3: gleicher Chunk, gleiches Modell nochmal           erwartet: 23505 chunk_embeddings_primary_key
INSERT INTO chunk_embeddings (document_id, position, model, embedding)
VALUES ((SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '1409.6928'), 0,
        'voyage-4', ARRAY[0.7, 0.8, 0.9]);

-- E4: Chunk gibt es nicht (position 99)                 erwartet: 23503 chunk_embeddings_chunks_foreign_key
INSERT INTO chunk_embeddings (document_id, position, model, embedding)
VALUES ((SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '1409.6928'), 99,
        'voyage-4', ARRAY[0.1, 0.2, 0.3]);

-- E5: Dokument und Position gibt es je für sich, die Kombination aber nicht
--     (semantic_scholar hat nur position 0, arxiv hat position 1)
--                                                       erwartet: 23503 chunk_embeddings_chunks_foreign_key
INSERT INTO chunk_embeddings (document_id, position, model, embedding)
VALUES ((SELECT id FROM documents WHERE source = 'semantic_scholar' AND source_id = '1409.6928'), 1,
        'voyage-4', ARRAY[0.1, 0.2, 0.3]);

-- E6: leerer Vektor                                     erwartet: 23514 chunk_embeddings_invalid_embedding
INSERT INTO chunk_embeddings (document_id, position, model, embedding)
VALUES ((SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '1409.6928'), 1,
        'voyage-4', '{}');

-- E7: Vektor fehlt                                      erwartet: 23502 (not-null)
INSERT INTO chunk_embeddings (document_id, position, model, embedding)
VALUES ((SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '1409.6928'), 1,
        'voyage-4', NULL);

-- E8: Modell fehlt                                      erwartet: 23502 (not-null)
INSERT INTO chunk_embeddings (document_id, position, model, embedding)
VALUES ((SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '1409.6928'), 1,
        NULL, ARRAY[0.1, 0.2, 0.3]);

-- E9: andere Vektorlänge (2 statt 3 Zahlen)             erwartet: ✅ (E29: Länge wird nicht geprüft)
INSERT INTO chunk_embeddings (document_id, position, model, embedding)
VALUES ((SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '1409.6928'), 1,
        'voyage-4', ARRAY[0.1, 0.2]);

-- E10: leerer Modellname                                erwartet: ✅ (bisher nicht verboten, siehe offene Frage)
INSERT INTO chunk_embeddings (document_id, position, model, embedding)
VALUES ((SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '1409.6928'), 1,
        '', ARRAY[0.1, 0.2, 0.3]);

-- Stand: erwartet 4 Zeilen (E1, E2, E9, E10)
SELECT document_id, position, model, embedding FROM chunk_embeddings ORDER BY document_id, position, model;

-- E11: Chunk löschen                                     erwartet: seine Vektoren verschwinden mit
DELETE FROM chunks
WHERE document_id = (SELECT id FROM documents WHERE source = 'arxiv' AND source_id = '1409.6928')
  AND position = 1;

-- erwartet: 2 Zeilen (E1, E2), die Vektoren zu position 1 sind weg
SELECT document_id, position, model FROM chunk_embeddings ORDER BY document_id, position, model;

-- E12: Kette documents → chunks → chunk_embeddings
-- 12a: Vektor für den Chunk von semantic_scholar anlegen      erwartet: ✅
INSERT INTO chunk_embeddings (document_id, position, model, embedding)
VALUES ((SELECT id FROM documents WHERE source = 'semantic_scholar' AND source_id = '1409.6928'), 0,
        'voyage-4', ARRAY[0.1, 0.2, 0.3]);

-- 12b: Dokument löschen
DELETE FROM documents WHERE source = 'semantic_scholar' AND source_id = '1409.6928';

-- 12c: erwartet: keine Chunks und keine Vektoren mehr zu diesem Dokument; übrig bleiben E1 und E2
SELECT document_id, position, model FROM chunk_embeddings ORDER BY document_id, position, model;
SELECT document_id, position FROM chunks ORDER BY document_id, position;

-- Aufräumen, wenn fertig:
-- DELETE FROM chunk_embeddings;
