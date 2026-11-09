INSERT INTO runs (run_at, variant, keywords, question, k, input_tokens, output_tokens, duration_ms)
VALUES (%(run_at)s, %(variant)s, %(keywords)s, %(question)s, %(k)s, %(input_tokens)s, %(output_tokens)s, %(duration_ms)s)
RETURNING id;
