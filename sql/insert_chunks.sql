INSERT INTO chunks (document_id, position, text)
SELECT %(document_id)s, c.position - 1, c.text
FROM unnest(%(texts)s) WITH ORDINALITY AS c(text, position);
