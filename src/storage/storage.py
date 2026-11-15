import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import psycopg
from psycopg.rows import dict_row

from sources import Document, SearchFilter

SQL_DIR = Path(__file__).resolve().parents[2] / "sql"
DEFAULT_DATABASE_URL = "postgresql:///algorithmusprojekt"


CACHE_MAX_AGE = timedelta(days=7)


class StorageError(Exception):
    """Raised when the database is unreachable, an SQL file is missing or a statement fails."""


@dataclass(frozen=True)
class Run:
    """One measurement run for the KPI evaluation."""
    run_at: datetime
    variant: str
    question: str
    input_tokens: int
    output_tokens: int
    duration_ms: int
    keywords: Optional[list[str]] = None
    k: Optional[int] = None


@dataclass(frozen=True)
class StoredDocument:
    """A document loaded from the database together with its storage fields."""
    id: int
    document: Document
    origin: str
    full_text: Optional[str]
    chunk_size: int
    overlap: int


def database_url() -> str:
    """Connection URL from DATABASE_URL, otherwise the local default database."""
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def connect(url: str = "") -> psycopg.Connection:
    """Opens a connection; failures become StorageError."""
    try:
        return psycopg.connect(url or database_url())
    except psycopg.OperationalError as error:
        raise StorageError(f"database not reachable: {error}") from error


def load_sql(name: str, sql_dir: Path = SQL_DIR) -> str:
    """Returns the content of sql/<name>.sql."""
    path = sql_dir / f"{name}.sql"
    if not path.is_file():
        raise StorageError(f"SQL file missing: {path.name}")
    return path.read_text(encoding="utf-8")


def apply_schema(connection: psycopg.Connection, sql_dir: Path = SQL_DIR) -> None:
    """Runs sql/schema.sql in one transaction."""
    with connection.transaction():
        connection.execute(load_sql("schema", sql_dir))


def execute(connection: psycopg.Connection, name: str, params: dict) -> psycopg.Cursor:
    """Runs sql/<name>.sql with the parameters in its own transaction; database errors become StorageError."""
    sql = load_sql(name)
    try:
        with connection.transaction():
            return connection.execute(sql, params)
    except psycopg.Error as error:
        raise StorageError(f"{name}.sql failed: {error}") from error


def normalize_key(values) -> list[str]:
    """Lowercases and sorts keywords or categories so that the cache compares equal searches (E13)."""
    return sorted(value.casefold() for value in values)


def document_params(document: Document, chunk_size: int, overlap: int, origin: str,
                    full_text: Optional[str]) -> dict:
    """Parameters for upsert_document.sql; empty strings become NULL."""
    return {
        "source": document.source,
        "source_id": document.id,
        "doi": document.doi or None,
        "title": document.title,
        "abstract": document.abstract or None,
        "authors": list(document.authors),
        "published": document.published,
        "url": document.url,
        "categories": list(document.categories),
        "journal_ref": document.journal_ref or None,
        "origin": origin,
        "full_text": full_text,
        "chunk_size": chunk_size,
        "overlap": overlap,
    }


def save_document(connection: psycopg.Connection, document: Document, chunk_size: int, overlap: int,
                  origin: str = "abstract", full_text: Optional[str] = None) -> int:
    """Inserts or updates a document and returns its database id."""
    params = document_params(document, chunk_size, overlap, origin, full_text)
    return execute(connection, "upsert_document", params).fetchone()[0]


def find_documents(connection: psycopg.Connection, document_ids: list[int]) -> list[StoredDocument]:
    """Documents in the order of document_ids; unknown ids are skipped, NULL becomes an empty string."""
    if not document_ids:
        return []
    with connection.cursor(row_factory=dict_row) as cursor:
        try:
            rows = cursor.execute(load_sql("find_documents"), {"document_ids": document_ids}).fetchall()
        except psycopg.Error as error:
            raise StorageError(f"find_documents.sql failed: {error}") from error
    by_id = {row["id"]: row for row in rows}
    return [stored_document(by_id[document_id]) for document_id in document_ids if document_id in by_id]


def stored_document(row: dict) -> StoredDocument:
    """Turns one row of find_documents.sql into a StoredDocument."""
    document = Document(id=row["source_id"], title=row["title"], abstract=row["abstract"] or "",
                        authors=tuple(row["authors"]), published=row["published"], url=row["url"],
                        source=row["source"], categories=tuple(row["categories"]),
                        journal_ref=row["journal_ref"] or "", doi=row["doi"] or "")
    return StoredDocument(row["id"], document, row["origin"], row["full_text"], row["chunk_size"], row["overlap"])


def save_chunks(connection: psycopg.Connection, document_id: int, texts: list[str]) -> None:
    """Replaces all chunks of a document; old embeddings are removed by CASCADE."""
    with connection.transaction():
        execute(connection, "delete_chunks", {"document_id": document_id})
        execute(connection, "insert_chunks", {"document_id": document_id, "texts": texts})


def find_chunks(connection: psycopg.Connection, document_ids: list[int]) -> list[tuple[int, int, str]]:
    """Chunks of the documents as (document_id, position, text), ordered by document and position."""
    if not document_ids:
        return []
    return execute(connection, "find_chunks", {"document_ids": document_ids}).fetchall()


def save_embedding(connection: psycopg.Connection, document_id: int, position: int, model: str,
                   embedding: list[float]) -> None:
    """Stores the vector of a chunk; an existing vector for the same model is kept."""
    if not embedding:
        raise ValueError("embedding must not be empty")
    execute(connection, "insert_embedding",
            {"document_id": document_id, "position": position, "model": model, "embedding": embedding})


def find_embeddings(connection: psycopg.Connection, document_ids: list[int],
                    model: str) -> dict[tuple[int, int], list[float]]:
    """Stored vectors of one model, keyed by (document_id, position)."""
    if not document_ids:
        return {}
    rows = execute(connection, "find_embeddings", {"document_ids": document_ids, "model": model}).fetchall()
    return {(document_id, position): embedding for document_id, position, embedding in rows}


def search_params(keywords: list[str], search_filter: SearchFilter) -> dict:
    """Normalized parameters shared by insert_search.sql and find_cached_search.sql."""
    return {
        "keywords": normalize_key(keywords),
        "published_from": search_filter.published_from,
        "published_to": search_filter.published_to,
        "categories": normalize_key(search_filter.categories),
        "peer_reviewed_only": search_filter.peer_reviewed_only,
    }


def save_search(connection: psycopg.Connection, keywords: list[str], search_filter: SearchFilter,
                document_ids: list[int]) -> None:
    """Stores a search with its documents in the order the source returned them."""
    execute(connection, "insert_search", {**search_params(keywords, search_filter), "document_ids": document_ids})


def find_cached_search(connection: psycopg.Connection, keywords: list[str], search_filter: SearchFilter,
                       max_age: timedelta = CACHE_MAX_AGE) -> list[int]:
    """Document ids of the newest equal search younger than max_age; empty if there is none."""
    params = {**search_params(keywords, search_filter), "max_age": max_age}
    return [row[0] for row in execute(connection, "find_cached_search", params).fetchall()]


def save_run(connection: psycopg.Connection, run: Run) -> int:
    """Stores a measurement run and returns its id."""
    params = {
        "run_at": run.run_at,
        "variant": run.variant,
        "keywords": run.keywords,
        "question": run.question,
        "k": run.k,
        "input_tokens": run.input_tokens,
        "output_tokens": run.output_tokens,
        "duration_ms": run.duration_ms,
    }
    return execute(connection, "insert_run", params).fetchone()[0]


def rate_run(connection: psycopg.Connection, run_id: int, found_source: bool) -> None:
    """Sets found_source of a run; an unknown id raises StorageError."""
    cursor = execute(connection, "update_run_found_source", {"id": run_id, "found_source": found_source})
    if cursor.rowcount == 0:
        raise StorageError(f"run {run_id} does not exist")


def kpi_by_variant(connection: psycopg.Connection) -> list[dict]:
    """Runs, average input tokens, average duration and hit rate per variant, numbers as float."""
    with connection.cursor(row_factory=dict_row) as cursor:
        try:
            rows = cursor.execute(load_sql("kpi_by_variant")).fetchall()
        except psycopg.Error as error:
            raise StorageError(f"kpi_by_variant.sql failed: {error}") from error
    return [{key: float(value) if key not in ("variant", "runs") and value is not None else value
             for key, value in row.items()} for row in rows]
