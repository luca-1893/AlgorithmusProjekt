INSERT INTO chunk_embeddings (embedding, position, model, document_id)
VALUES (%(embedding)s, %(position)s, %(model)s, %(document_id)s)
ON CONFLICT (position, document_id, model) DO NOTHING;
