-- Testfälle für die Regeln in documents.
-- Jeden Insert einzeln ausführen (Cursor hinein, ⌘ + Enter) und vorher die Vorhersage eintragen.

-- 1: gültiges Dokument, origin = 'pdf' mit Volltext
-- Vorhersage:
INSERT INTO documents (source, source_id, doi, title, abstract, authors, published, url,
                       categories, journal_ref, origin, full_text, chunk_size, overlap)
VALUES ('arxiv', '1409.6928', '10.1000/beispiel.1', 'Beispielpaper A', 'Kurzfassung A',
        ARRAY['Ada Lovelace', 'Alan Turing'], '2014-09-24', 'https://arxiv.org/abs/1409.6928v1',
        ARRAY['cs.SE'], NULL, 'pdf', 'Volltext A', 200, 40);

-- 2: gleiches source + source_id nochmal
-- Vorhersage:
INSERT INTO documents (source, source_id, doi, title, abstract, authors, published, url,
                       categories, journal_ref, origin, full_text, chunk_size, overlap)
VALUES ('arxiv', '1409.6928', '10.1000/beispiel.1', 'Beispielpaper A, Version 2', 'Kurzfassung A',
        ARRAY['Ada Lovelace', 'Alan Turing'], '2014-09-24', 'https://arxiv.org/abs/1409.6928v2',
        ARRAY['cs.SE'], NULL, 'pdf', 'Volltext A', 200, 40);

-- 3: gleiche source_id, andere source
-- Vorhersage:
INSERT INTO documents (source, source_id, doi, title, abstract, authors, published, url,
                       categories, journal_ref, origin, full_text, chunk_size, overlap)
VALUES ('semantic_scholar', '1409.6928', NULL, 'Beispielpaper B', 'Kurzfassung B',
        ARRAY['Grace Hopper'], '2015-01-10', 'https://example.org/papers/1409.6928',
        ARRAY['cs.AI'], NULL, 'html', 'Volltext B', 200, 40);

-- 4: origin großgeschrieben
-- Vorhersage:
INSERT INTO documents (source, source_id, doi, title, abstract, authors, published, url,
                       categories, journal_ref, origin, full_text, chunk_size, overlap)
VALUES ('arxiv', '2001.00004', NULL, 'Beispielpaper C', 'Kurzfassung C',
        ARRAY['Grace Hopper'], '2020-01-01', 'https://arxiv.org/abs/2001.00004v1',
        ARRAY['cs.SE'], NULL, 'PDF', 'Volltext C', 200, 40);

-- 5: origin = 'abstract', aber mit Volltext
-- Vorhersage:
INSERT INTO documents (source, source_id, doi, title, abstract, authors, published, url,
                       categories, journal_ref, origin, full_text, chunk_size, overlap)
VALUES ('arxiv', '2001.00005', NULL, 'Beispielpaper D', 'Kurzfassung D',
        ARRAY['Grace Hopper'], '2020-01-01', 'https://arxiv.org/abs/2001.00005v1',
        ARRAY['cs.SE'], NULL, 'abstract', 'Volltext D', 200, 40);

-- 6: origin = 'html', aber ohne Volltext
-- Vorhersage:
INSERT INTO documents (source, source_id, doi, title, abstract, authors, published, url,
                       categories, journal_ref, origin, full_text, chunk_size, overlap)
VALUES ('arxiv', '2001.00006', NULL, 'Beispielpaper E', 'Kurzfassung E',
        ARRAY['Grace Hopper'], '2020-01-01', 'https://arxiv.org/abs/2001.00006v1',
        ARRAY['cs.SE'], NULL, 'html', NULL, 200, 40);

-- 7: overlap = chunk_size
-- Vorhersage:
INSERT INTO documents (source, source_id, doi, title, abstract, authors, published, url,
                       categories, journal_ref, origin, full_text, chunk_size, overlap)
VALUES ('arxiv', '2001.00007', NULL, 'Beispielpaper F', 'Kurzfassung F',
        ARRAY['Grace Hopper'], '2020-01-01', 'https://arxiv.org/abs/2001.00007v1',
        ARRAY['cs.SE'], NULL, 'pdf', 'Volltext F', 200, 200);

-- 8: doi, journal_ref, authors und categories weggelassen
-- Vorhersage (und was steht danach in authors und categories?):
INSERT INTO documents (source, source_id, title, abstract, published, url,
                       origin, full_text, chunk_size, overlap)
VALUES ('arxiv', '2001.00008', 'Beispielpaper G', NULL, '2020-01-01',
        'https://arxiv.org/abs/2001.00008v1', 'abstract', NULL, 200, 40);

-- Ergebnis ansehen: Welche IDs haben die Zeilen, und warum gibt es Lücken?
SELECT id, source, source_id, origin, full_text IS NULL AS ohne_volltext, authors, categories, fetched_at
FROM documents
ORDER BY id;

-- Aufräumen, wenn fertig:
-- DELETE FROM documents;
