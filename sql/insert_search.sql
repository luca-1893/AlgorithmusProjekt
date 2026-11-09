WITH new AS (
    INSERT INTO searches (keywords, published_from, published_to, categories, peer_reviewed_only)
        VALUES (
                   %(keywords)s,
                   %(published_from)s,
                   %(published_to)s,
                   %(categories)s,
                   %(peer_reviewed_only)s
               )
        RETURNING id
)
INSERT INTO search_documents (search_id, document_id, position)
SELECT new.id, d.document_id, d.position - 1
FROM new, unnest(%(document_ids)s) WITH ORDINALITY AS d(document_id, position);