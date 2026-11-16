SELECT DISTINCT ON (c.text) c.text, e.embedding
FROM chunks c
JOIN chunk_embeddings e ON e.document_id = c.document_id AND e.position = c.position
WHERE c.text = ANY(%(texts)s::text[])
  AND e.model = %(model)s;
