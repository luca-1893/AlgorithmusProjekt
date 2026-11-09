import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HAS_PSYCOPG = importlib.util.find_spec("psycopg") is not None
if HAS_PSYCOPG:
    from storage.storage import DEFAULT_DATABASE_URL, StorageError, apply_schema, connect, database_url, load_sql

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql:///algorithmusprojekt_test")


def database_available():
    if not HAS_PSYCOPG:
        return False
    try:
        connect(TEST_DATABASE_URL).close()
        return True
    except StorageError:
        return False


@unittest.skipUnless(HAS_PSYCOPG, "psycopg missing, use .venv")
class TestStorageConfig(unittest.TestCase):
    def test_database_url_default(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertEqual(database_url(), DEFAULT_DATABASE_URL)

    def test_database_url_from_environment(self):
        with mock.patch.dict("os.environ", {"DATABASE_URL": "postgresql://server/db"}):
            self.assertEqual(database_url(), "postgresql://server/db")

    def test_load_sql_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "query.sql").write_text("SELECT 1;", encoding="utf-8")
            self.assertEqual(load_sql("query", Path(directory)), "SELECT 1;")

    def test_load_sql_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(StorageError, "schema.sql"):
                load_sql("schema", Path(directory))

    def test_connect_unreachable(self):
        with self.assertRaises(StorageError):
            connect("postgresql://127.0.0.1:1/nothing?connect_timeout=1")


@unittest.skipUnless(database_available(), "test database not reachable")
class TestStorageDatabase(unittest.TestCase):
    def test_apply_schema_runs_file(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "schema.sql").write_text("SELECT 1;", encoding="utf-8")
            with connect(TEST_DATABASE_URL) as connection:
                apply_schema(connection, Path(directory))

    def test_connect_test_database(self):
        with connect(TEST_DATABASE_URL) as connection:
            self.assertEqual(connection.execute("SELECT 1").fetchone(), (1,))
