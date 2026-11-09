SELECT document_id
FROM search_documents
WHERE search_id = (
    SELECT id
    FROM searches
    WHERE keywords = %(keywords)s
    AND published_from IS NOT DISTINCT FROM %(published_from)s
    AND published_to IS NOT DISTINCT FROM %(published_to)s
    AND categories = %(categories)s
    AND peer_reviewed_only = %(peer_reviewed_only)s
    AND searched_at >= now() - %(max_age)s
ORDER BY searched_at DESC
LIMIT 1
    )
ORDER BY position;