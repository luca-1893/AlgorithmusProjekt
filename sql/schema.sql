CREATE TABLE IF NOT EXISTS documents (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source text not null,
    source_id text not null,
    doi text,
    title text not null,
    abstract text,
    authors text[] not null DEFAULT '{}',
    published date not null,
    url text not null,
    categories text[] not null DEFAULT '{}',
    journal_ref text,
    origin text not null ,
    full_text text,
    chunk_size integer not null,
    overlap integer not null ,
    fetched_at timestamptz not null default now(),

    CHECK (origin in ('html', 'pdf', 'abstract')),
    CHECK (chunk_size > 0),
    CHECK  (overlap >= 0 and overlap < chunk_size),
    CHECK ((full_text IS NULL) = (origin = 'abstract')),
    UNIQUE (source, source_id)
    )