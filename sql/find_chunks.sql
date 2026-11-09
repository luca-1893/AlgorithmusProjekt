SELECT document_id, position, text
FROM chunks
WHERE document_id = ANY(%(document_ids)s)
ORDER BY document_id, position;
