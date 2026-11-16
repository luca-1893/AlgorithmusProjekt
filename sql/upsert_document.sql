INSERT INTO documents (source, source_id, doi, title, abstract, authors, published, url, categories, journal_ref, origin, full_text, chunk_size, overlap)
VALUES (%(source)s,
        %(source_id)s,
        %(doi)s,
        %(title)s,
        %(abstract)s,
        %(authors)s,
        %(published)s,
        %(url)s,
        %(categories)s,
        %(journal_ref)s,
        %(origin)s,
        %(full_text)s,
        %(chunk_size)s,
        %(overlap)s
        )


ON CONFLICT (source, source_id ) DO UPDATE
SET doi = EXCLUDED.doi,
    title = EXCLUDED.title,
    abstract = EXCLUDED.abstract,
    authors = EXCLUDED.authors,
    published = EXCLUDED.published,
    url = EXCLUDED.url,
    categories = EXCLUDED.categories,
    journal_ref = EXCLUDED.journal_ref,
    origin = EXCLUDED.origin,
    full_text = EXCLUDED.full_text,
    chunk_size = EXCLUDED.chunk_size,
    overlap = EXCLUDED.overlap,
    fetched_at = now()
RETURNING id;