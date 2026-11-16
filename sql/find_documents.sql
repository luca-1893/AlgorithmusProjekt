SELECT id, source, source_id, doi, title, abstract, authors, published, url, categories, journal_ref,
       origin, full_text, chunk_size, overlap
FROM documents
WHERE id = ANY(%(document_ids)s);
