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
    model text NOT NULL ,
    embedding real[] NOT NULL ,

    CONSTRAINT chunk_embeddings_chunks_foreign_key FOREIGN KEY (document_id, position) REFERENCES chunks (document_id, position) ON DELETE CASCADE ,
    CONSTRAINT chunk_embeddings_primary_key PRIMARY KEY (document_id, position, model),
    CONSTRAINT chunk_embeddings_invalid_embedding CHECK ( embedding <> '{}' ),
    CONSTRAINT chunk_embeddings_invalid_model CHECK ( model <> '' )
);

CREATE TABLE IF NOT EXISTS searches (
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    keywords text[] NOT NULL,
    published_from date,
    published_to date,
    categories text[] NOT NULL DEFAULT '{}',
    peer_reviewed_only boolean NOT NULL,
    searched_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS search_documents (
    search_id   integer NOT NULL,
    document_id integer NOT NULL,
    position    integer NOT NULL,

    CONSTRAINT search_documents_searches_foreign_key FOREIGN KEY (search_id) REFERENCES searches (id) ON DELETE CASCADE,
    CONSTRAINT search_documents_document_foreign_key FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE,
    CONSTRAINT search_documents_primary_key PRIMARY KEY (search_id, document_id)
);

CREATE TABLE IF NOT EXISTS runs (
    id integer NOT NULL GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_at timestamptz NOT NULL,
    variant text NOT NULL,
    keywords text[],
    question text NOT NULL,
    k integer,
    input_tokens integer NOT NULL,
    output_tokens integer NOT NULL,
    duration_ms integer NOT NULL,
    found_source boolean,

    CONSTRAINT runs_invalid_variant CHECK ( variant IN ('agent_websearch', 'bm25', 'hybrid')),
    CONSTRAINT runs_invalid_keywords CHECK ( (keywords IS NULL) = (variant = 'agent_websearch')),
    CONSTRAINT runs_invalid_k CHECK ( k BETWEEN 1 AND 20),
    CONSTRAINT runs_k_null CHECK ( (k IS NULL) = (variant = 'agent_websearch')),
    CONSTRAINT runs_invalid_input_tokens CHECK (input_tokens >= 0),
    CONSTRAINT runs_invalid_output_tokens CHECK (output_tokens >= 0),
    CONSTRAINT runs_invalid_duration_ms CHECK (duration_ms >= 0)
);
