SELECT document_id, position, embedding
FROM chunk_embeddings
WHERE document_id = ANY(%(document_ids)s)
  AND model = %(model)s;
