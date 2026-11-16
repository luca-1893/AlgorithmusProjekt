-- Testfälle für die Regeln in searches und search_documents.
-- Eigenständig: legt zwei eigene Dokumente mit source = 'test' an und räumt am Ende auf.
-- IDs werden über die Werte nachgeschlagen, nicht als Zahl angenommen.
-- Jeden Insert einzeln ausführen (Cursor hinein, ⌘ + Enter).

-- Vorbereitung: zwei Testdokumente
INSERT INTO documents (source, source_id, title, published, url, origin, chunk_size, overlap)
VALUES ('test', 'doc-a', 'Testdokument A', '2024-01-01', 'https://example.org/a', 'abstract', 200, 40),
       ('test', 'doc-b', 'Testdokument B', '2024-01-02', 'https://example.org/b', 'abstract', 200, 40);

-- ===== searches =====

-- S1: gültige Suche ohne Filter                          erwartet: ✅, categories = {}, searched_at gesetzt
INSERT INTO searches (keywords, peer_reviewed_only)
VALUES ('{semantics,uml}', false)
RETURNING id, categories, searched_at;

-- S2: gültige Suche mit Zeitraum und Kategorien          erwartet: ✅
INSERT INTO searches (keywords, published_from, published_to, categories, peer_reviewed_only)
VALUES ('{bm25,retrieval}', '2020-01-01', NULL, '{cs.ir}', true)
RETURNING id;

-- S3: dieselbe Suche wie S1 noch einmal                   erwartet: ✅ (E17: neue Zeile, kein UNIQUE)
INSERT INTO searches (keywords, peer_reviewed_only)
VALUES ('{semantics,uml}', false);

-- S4: Schlagwörter fehlen                                erwartet: 23502 (not-null keywords)
INSERT INTO searches (keywords, peer_reviewed_only)
VALUES (NULL, false);

-- S5: peer_reviewed_only fehlt                           erwartet: 23502 (not-null peer_reviewed_only)
INSERT INTO searches (keywords, peer_reviewed_only)
VALUES ('{uml}', NULL);

-- S6: id selbst vorgeben                                 erwartet: 428C9 (GENERATED ALWAYS)
INSERT INTO searches (id, keywords, peer_reviewed_only)
VALUES (999, '{uml}', false);

-- S7: leere Schlagwortliste                              erwartet: ✅ (bisher nicht verboten, offene Frage)
INSERT INTO searches (keywords, peer_reviewed_only)
VALUES ('{}', false);

-- S8: Zeitraum verdreht (von nach bis)                   erwartet: ✅ (bisher nicht verboten, offene Frage)
INSERT INTO searches (keywords, published_from, published_to, peer_reviewed_only)
VALUES ('{uml}', '2025-01-01', '2020-01-01', false);

-- ===== search_documents =====
-- Für die Zuordnungen wird die Suche S2 über ihre Schlagwörter gefunden.

-- SD1: Dokument A auf Platz 0                            erwartet: ✅
INSERT INTO search_documents (search_id, document_id, position)
VALUES ((SELECT id FROM searches WHERE keywords = '{bm25,retrieval}'),
        (SELECT id FROM documents WHERE source = 'test' AND source_id = 'doc-a'), 0);

-- SD2: Dokument B auf Platz 1                            erwartet: ✅
INSERT INTO search_documents (search_id, document_id, position)
VALUES ((SELECT id FROM searches WHERE keywords = '{bm25,retrieval}'),
        (SELECT id FROM documents WHERE source = 'test' AND source_id = 'doc-b'), 1);

-- SD3: Dokument A noch einmal in derselben Suche          erwartet: 23505 search_documents_primary_key
INSERT INTO search_documents (search_id, document_id, position)
VALUES ((SELECT id FROM searches WHERE keywords = '{bm25,retrieval}'),
        (SELECT id FROM documents WHERE source = 'test' AND source_id = 'doc-a'), 2);

-- SD4: Suche gibt es nicht                               erwartet: 23503 search_documents_searches_foreign_key
INSERT INTO search_documents (search_id, document_id, position)
VALUES (999999, (SELECT id FROM documents WHERE source = 'test' AND source_id = 'doc-a'), 0);

-- SD5: Dokument gibt es nicht                            erwartet: 23503 search_documents_document_foreign_key
INSERT INTO search_documents (search_id, document_id, position)
VALUES ((SELECT id FROM searches WHERE keywords = '{bm25,retrieval}'), 999999, 0);

-- SD6: position fehlt                                    erwartet: 23502 (not-null position)
INSERT INTO search_documents (search_id, document_id, position)
VALUES ((SELECT id FROM searches WHERE keywords = '{semantics,uml}' ORDER BY id LIMIT 1),
        (SELECT id FROM documents WHERE source = 'test' AND source_id = 'doc-a'), NULL);

-- SD7: negative position                                 erwartet: ✅ (bisher nicht verboten, offene Frage)
INSERT INTO search_documents (search_id, document_id, position)
VALUES ((SELECT id FROM searches WHERE keywords = '{semantics,uml}' ORDER BY id LIMIT 1),
        (SELECT id FROM documents WHERE source = 'test' AND source_id = 'doc-a'), -1);

-- Stand: erwartet 3 Zuordnungen (SD1, SD2, SD7)
SELECT search_id, document_id, position FROM search_documents ORDER BY search_id, position;

-- SD8: Suche S2 löschen                                  erwartet: ihre 2 Zuordnungen verschwinden, die Dokumente bleiben (E15)
DELETE FROM searches WHERE keywords = '{bm25,retrieval}';
SELECT count(*) AS zuordnungen FROM search_documents;                        -- erwartet: 1
SELECT count(*) AS testdokumente FROM documents WHERE source = 'test';       -- erwartet: 2

-- SD9: Dokument A löschen                                erwartet: seine Zuordnung verschwindet (E16)
DELETE FROM documents WHERE source = 'test' AND source_id = 'doc-a';
SELECT count(*) AS zuordnungen FROM search_documents;                        -- erwartet: 0

-- Aufräumen
DELETE FROM searches;
DELETE FROM documents WHERE source = 'test';
