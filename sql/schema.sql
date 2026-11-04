CREATE TABLE IF NOT EXISTS documents (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source text NOT NULL,
    source_id text NOT NULL,
    doi text,
    title text NOT NULL,
    abstract text,
    authors text[] NOT NULL DEFAULT '{}',
    published date NOT NULL,
    url text NOT NULL,
    categories text[] NOT NULL DEFAULT '{}',
    journal_ref text,
    origin text NOT NULL,
    full_text text,
    chunk_size integer NOT NULL,
    overlap integer NOT NULL,
    fetched_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT documents_invalid_origin CHECK (origin IN ('html', 'pdf', 'abstract')),
    CONSTRAINT documents_invalid_chunk_size CHECK (chunk_size > 0),
    CONSTRAINT documents_invalid_overlap CHECK (overlap >= 0 AND overlap < chunk_size),
    CONSTRAINT documents_invalid_full_text CHECK ((full_text IS NULL) = (origin = 'abstract')),
    CONSTRAINT documents_source_unique UNIQUE (source, source_id)
    );


CREATE TABLE IF NOT EXISTS chunks (
    document_id integer NOT NULL,
    position integer NOT NULL ,
    text text NOT NULL ,

    CONSTRAINT chunks_primary_key PRIMARY KEY (document_id, position),
    CONSTRAINT chunks_document_foreign_key FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    CONSTRAINT chunks_invalid_position CHECK ( position >= 0),
    CONSTRAINT chunks_invalid_text CHECK (text <> '')
);

CREATE TABLE IF NOT EXISTS chunk_embeddings (
    document_id integer NOT NULL ,
    position integer NOT NULL ,
    model text PRIMARY KEY NOT NULL ,
    embedding real[] NOT NULL ,

    CONSTRAINT chunk_embeddings_missing_document_id CHECK (document_id IS NOT NULL),
    CONSTRAINT chunk_embeddings_missing_position CHECK ( position IS NOT NULL ),
    CONSTRAINT chunk_embeddings_missing_embedding CHECK ( embedding IS NOT NULL ),
    CONSTRAINT chunk_embeddings_missing_model CHECK ( model IS NOT NULL ),
    CONSTRAINT chunk_foreign_key_document_id FOREIGN KEY (document_id) REFERENCES chunks (document_id) ON DELETE CASCADE ,
    CONSTRAINT chunk_foreign_key_position FOREIGN KEY (position) REFERENCES chunks (position) ON DELETE CASCADE

);