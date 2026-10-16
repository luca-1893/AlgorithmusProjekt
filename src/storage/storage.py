import os
from pathlib import Path

import psycopg

SQL_DIR = Path(__file__).resolve().parents[2] / "sql"
DEFAULT_DATABASE_URL = "postgresql:///algorithmusprojekt"


class StorageError(Exception):
    """Raised when the database is unreachable or an SQL file is missing."""


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
