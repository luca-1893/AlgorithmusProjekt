import importlib.util
import os
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import mock

HAS_PSYCOPG = importlib.util.find_spec("psycopg") is not None
if HAS_PSYCOPG:
    from storage.storage import (DEFAULT_DATABASE_URL, Run, StorageError, apply_schema, connect, database_url,
                                 StoredDocument, document_params, find_cached_search, find_chunks, find_documents,
                                 find_embeddings, kpi_by_variant,
                                 load_sql, normalize_key, rate_run, save_chunks, save_document, save_embedding,
                                 save_run, save_search)
from sources import Document, SearchFilter

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


def make_document(source_id="2401.00001", doi="", journal_ref=""):
    return Document(id=source_id, title="Titel", abstract="Abstract", authors=("Ada", "Bob"),
                    published=date(2024, 1, 2), url=f"https://arxiv.org/abs/{source_id}", source="arxiv",
                    categories=("cs.IR",), journal_ref=journal_ref, doi=doi)


def make_run(**changes):
    values = dict(run_at=datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc), variant="bm25",
                  question="Frage?", input_tokens=1000, output_tokens=200, duration_ms=1500,
                  keywords=["bm25"], k=5)
    values.update(changes)
    return Run(**values)


@unittest.skipUnless(HAS_PSYCOPG, "psycopg missing, use .venv")
class TestStorageHelpers(unittest.TestCase):
    def test_normalize_key_lowercase_and_sorted(self):
        self.assertEqual(normalize_key(["UML", "bm25", "Class Diagram"]), ["bm25", "class diagram", "uml"])

    def test_normalize_key_same_result_for_different_order(self):
        self.assertEqual(normalize_key(["B", "a"]), normalize_key(["A", "b"]))

    def test_normalize_key_empty(self):
        self.assertEqual(normalize_key([]), [])

    def test_document_params_empty_strings_become_null(self):
        params = document_params(make_document(), 200, 40, "abstract", None)
        self.assertIsNone(params["doi"])
        self.assertIsNone(params["journal_ref"])

    def test_document_params_fields(self):
        params = document_params(make_document(doi="10.1/x", journal_ref="J"), 200, 40, "abstract", None)
        self.assertEqual(params["source_id"], "2401.00001")
        self.assertEqual(params["authors"], ["Ada", "Bob"])
        self.assertEqual(params["categories"], ["cs.IR"])
        self.assertEqual(params["doi"], "10.1/x")
        self.assertEqual((params["chunk_size"], params["overlap"]), (200, 40))

    def test_save_embedding_rejects_empty_vector(self):
        with self.assertRaises(ValueError):
            save_embedding(None, 1, 0, "voyage-4", [])


@unittest.skipUnless(database_available(), "test database not reachable")
class TestStorageRepository(unittest.TestCase):
    def setUp(self):
        self.connection = connect(TEST_DATABASE_URL)
        apply_schema(self.connection)
        self.outer = self.connection.transaction(force_rollback=True)
        self.outer.__enter__()

    def tearDown(self):
        self.outer.__exit__(None, None, None)
        self.connection.close()

    def test_save_document_returns_id(self):
        self.assertIsInstance(save_document(self.connection, make_document(), 200, 40), int)

    def test_save_document_twice_keeps_id_and_updates(self):
        first = save_document(self.connection, make_document(), 200, 40)
        second = save_document(self.connection, make_document(doi="10.1/neu"), 200, 40)
        self.assertEqual(first, second)
        doi = self.connection.execute("SELECT doi FROM documents WHERE id = %s", (first,)).fetchone()[0]
        self.assertEqual(doi, "10.1/neu")

    def test_save_document_full_text_without_text_fails(self):
        with self.assertRaisesRegex(StorageError, "documents_invalid_full_text"):
            save_document(self.connection, make_document(), 200, 40, origin="pdf")

    def test_save_chunks_and_find_in_order(self):
        document_id = save_document(self.connection, make_document(), 200, 40)
        save_chunks(self.connection, document_id, ["eins", "zwei", "drei"])
        self.assertEqual(find_chunks(self.connection, [document_id]),
                         [(document_id, 0, "eins"), (document_id, 1, "zwei"), (document_id, 2, "drei")])

    def test_save_chunks_replaces_old_chunks(self):
        document_id = save_document(self.connection, make_document(), 200, 40)
        save_chunks(self.connection, document_id, ["alt1", "alt2", "alt3"])
        save_chunks(self.connection, document_id, ["neu"])
        self.assertEqual(find_chunks(self.connection, [document_id]), [(document_id, 0, "neu")])

    def test_save_chunks_empty_text_fails(self):
        document_id = save_document(self.connection, make_document(), 200, 40)
        with self.assertRaisesRegex(StorageError, "chunks_invalid_text"):
            save_chunks(self.connection, document_id, ["gut", ""])

    def test_find_chunks_empty_ids(self):
        self.assertEqual(find_chunks(self.connection, []), [])

    def test_embeddings_round_trip_and_duplicate_ignored(self):
        document_id = save_document(self.connection, make_document(), 200, 40)
        save_chunks(self.connection, document_id, ["eins", "zwei"])
        save_embedding(self.connection, document_id, 0, "voyage-4", [0.5, 0.25])
        save_embedding(self.connection, document_id, 0, "voyage-4", [9.0, 9.0])
        self.assertEqual(find_embeddings(self.connection, [document_id], "voyage-4"),
                         {(document_id, 0): [0.5, 0.25]})

    def test_find_embeddings_other_model_empty(self):
        document_id = save_document(self.connection, make_document(), 200, 40)
        save_chunks(self.connection, document_id, ["eins"])
        save_embedding(self.connection, document_id, 0, "voyage-4", [0.5])
        self.assertEqual(find_embeddings(self.connection, [document_id], "anderes-modell"), {})

    def test_save_embedding_unknown_chunk_fails(self):
        document_id = save_document(self.connection, make_document(), 200, 40)
        with self.assertRaises(StorageError):
            save_embedding(self.connection, document_id, 7, "voyage-4", [0.5])

    def test_cached_search_found_with_other_order_and_case(self):
        first = save_document(self.connection, make_document("2401.00001"), 200, 40)
        second = save_document(self.connection, make_document("2401.00002"), 200, 40)
        save_search(self.connection, ["UML", "BM25"], SearchFilter(), [second, first])
        self.assertEqual(find_cached_search(self.connection, ["bm25", "uml"], SearchFilter()), [second, first])

    def test_cached_search_other_filter_not_found(self):
        document_id = save_document(self.connection, make_document(), 200, 40)
        save_search(self.connection, ["uml"], SearchFilter(), [document_id])
        self.assertEqual(find_cached_search(self.connection, ["uml"], SearchFilter(peer_reviewed_only=True)), [])

    def test_cached_search_too_old_not_found(self):
        document_id = save_document(self.connection, make_document(), 200, 40)
        save_search(self.connection, ["uml"], SearchFilter(), [document_id])
        self.connection.execute("UPDATE searches SET searched_at = now() - interval '8 days'")
        self.assertEqual(find_cached_search(self.connection, ["uml"], SearchFilter()), [])

    def test_save_run_and_rate(self):
        run_id = save_run(self.connection, make_run())
        rate_run(self.connection, run_id, True)
        found = self.connection.execute("SELECT found_source FROM runs WHERE id = %s", (run_id,)).fetchone()[0]
        self.assertTrue(found)

    def test_rate_unknown_run_fails(self):
        with self.assertRaises(StorageError):
            rate_run(self.connection, -1, True)

    def test_save_run_invalid_variant_fails(self):
        with self.assertRaisesRegex(StorageError, "runs_invalid_variant"):
            save_run(self.connection, make_run(variant="ohne_tool"))

    def test_kpi_by_variant_floats_and_unrated_none(self):
        self.connection.execute("DELETE FROM runs")
        rated = save_run(self.connection, make_run(input_tokens=1000))
        save_run(self.connection, make_run(input_tokens=2000))
        rate_run(self.connection, rated, True)
        save_run(self.connection, make_run(variant="agent_websearch", keywords=None, k=None))
        kpi = {row["variant"]: row for row in kpi_by_variant(self.connection)}
        self.assertEqual(kpi["bm25"]["runs"], 2)
        self.assertEqual(kpi["bm25"]["avg_input_tokens"], 1500.0)
        self.assertIsInstance(kpi["bm25"]["avg_input_tokens"], float)
        self.assertEqual(kpi["bm25"]["hit_rate"], 1.0)
        self.assertIsNone(kpi["agent_websearch"]["hit_rate"])


@unittest.skipUnless(database_available(), "test database not reachable")
class TestFindDocuments(unittest.TestCase):
    def setUp(self):
        self.connection = connect(TEST_DATABASE_URL)
        self.outer = self.connection.transaction(force_rollback=True)
        self.outer.__enter__()

    def tearDown(self):
        self.outer.__exit__(None, None, None)
        self.connection.close()

    def test_find_documents_round_trip(self):
        original = make_document(doi="10.1/x", journal_ref="J")
        document_id = save_document(self.connection, original, 200, 40)
        stored = find_documents(self.connection, [document_id])
        self.assertEqual(stored, [StoredDocument(document_id, original, "abstract", None, 200, 40)])

    def test_find_documents_null_becomes_empty_string(self):
        document_id = save_document(self.connection, make_document(), 200, 40)
        document = find_documents(self.connection, [document_id])[0].document
        self.assertEqual((document.doi, document.journal_ref), ("", ""))

    def test_find_documents_keeps_given_order(self):
        first = save_document(self.connection, make_document("2401.00001"), 200, 40)
        second = save_document(self.connection, make_document("2401.00002"), 200, 40)
        ids = [stored.id for stored in find_documents(self.connection, [second, first])]
        self.assertEqual(ids, [second, first])

    def test_find_documents_unknown_id_skipped(self):
        document_id = save_document(self.connection, make_document(), 200, 40)
        self.assertEqual([stored.id for stored in find_documents(self.connection, [-1, document_id])], [document_id])

    def test_find_documents_empty_ids(self):
        self.assertEqual(find_documents(self.connection, []), [])
