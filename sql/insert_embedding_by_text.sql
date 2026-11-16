INSERT INTO chunk_embeddings (document_id, position, model, embedding)
SELECT document_id, position, %(model)s, %(embedding)s::real[]
FROM chunks
WHERE text = %(text)s
ON CONFLICT (document_id, position, model) DO NOTHING;
