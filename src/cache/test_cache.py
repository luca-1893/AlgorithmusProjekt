import importlib.util
import os
import unittest
from datetime import date

from sources import Document, SearchFilter, Source, SourceError

HAS_PSYCOPG = importlib.util.find_spec("psycopg") is not None
if HAS_PSYCOPG:
    from cache.cache import CACHE_HIT, CACHE_UNAVAILABLE, CachedSource
    from storage.storage import StorageError, connect

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql:///algorithmusprojekt_test")
TEST_SOURCE = "testcache"
KEYWORD = "cachetest"


def make_document(number):
    return Document(f"9999.{number:05d}", f"Titel {number}", f"Abstract {number}", ("Ada",),
                    date(2024, 1, number), f"https://arxiv.org/abs/9999.{number:05d}", TEST_SOURCE)


class FakeSource(Source):
    name = "fake"

    def __init__(self, documents=(), error=None):
        self.documents = list(documents)
        self.error = error
        self.calls = 0

    def search(self, keywords, max_results, search_filter=None):
        self.calls += 1
        if self.error:
            raise self.error
        return self.documents[:max_results]


def unreachable():
    raise StorageError("database not reachable")


def database_available():
    if not HAS_PSYCOPG:
        return False
    try:
        connect(TEST_DATABASE_URL).close()
        return True
    except StorageError:
        return False


@unittest.skipUnless(HAS_PSYCOPG, "psycopg missing, use .venv")
class TestCachedSourceWithoutDatabase(unittest.TestCase):
    def test_is_a_source(self):
        self.assertIsInstance(CachedSource(FakeSource(), connect=unreachable), Source)

    def test_database_unreachable_falls_back_to_source(self):
        inner = FakeSource([make_document(1), make_document(2)])
        cached = CachedSource(inner, connect=unreachable)
        documents = cached.search([KEYWORD], 2)
        self.assertEqual([document.id for document in documents], ["9999.00001", "9999.00002"])
        self.assertEqual(inner.calls, 1)
        self.assertEqual(cached.notes, (CACHE_UNAVAILABLE,))

    def test_source_error_propagates(self):
        cached = CachedSource(FakeSource(error=SourceError("down")), connect=unreachable)
        with self.assertRaises(SourceError):
            cached.search([KEYWORD], 2)

    def test_default_notes_empty(self):
        self.assertEqual(CachedSource(FakeSource(), connect=unreachable).notes, ())


@unittest.skipUnless(database_available(), "test database not reachable")
class TestCachedSourceWithDatabase(unittest.TestCase):
    def setUp(self):
        self.inner = FakeSource([make_document(1), make_document(2), make_document(3)])
        self.cached = CachedSource(self.inner, connect=lambda: connect(TEST_DATABASE_URL))
        self.cleanup()

    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        with connect(TEST_DATABASE_URL) as connection:
            connection.execute("DELETE FROM searches WHERE %s = ANY(keywords)", (KEYWORD,))
            connection.execute("DELETE FROM documents WHERE source = %s", (TEST_SOURCE,))

    def count(self, sql):
        with connect(TEST_DATABASE_URL) as connection:
            return connection.execute(sql, (TEST_SOURCE,)).fetchone()[0]

    def test_miss_asks_source_and_saves(self):
        self.cached.search([KEYWORD, "uml"], 2)
        self.assertEqual(self.inner.calls, 1)
        self.assertEqual(self.cached.notes, ())
        self.assertEqual(self.count("SELECT count(*) FROM documents WHERE source = %s"), 2)
        self.assertEqual(self.count("SELECT count(*) FROM search_documents JOIN documents ON id = document_id "
                                    "WHERE source = %s"), 2)

    def test_hit_skips_source_and_keeps_order(self):
        first = self.cached.search([KEYWORD, "uml"], 2)
        second = self.cached.search(["UML", KEYWORD.upper()], 2)
        self.assertEqual(self.inner.calls, 1)
        self.assertEqual(second, first)
        self.assertEqual(self.cached.notes, (CACHE_HIT,))

    def test_more_results_than_cached_asks_source_again(self):
        self.cached.search([KEYWORD], 2)
        documents = self.cached.search([KEYWORD], 3)
        self.assertEqual(self.inner.calls, 2)
        self.assertEqual(len(documents), 3)

    def test_fewer_results_than_cached_uses_cache(self):
        self.cached.search([KEYWORD], 3)
        documents = self.cached.search([KEYWORD], 2)
        self.assertEqual(self.inner.calls, 1)
        self.assertEqual([document.id for document in documents], ["9999.00001", "9999.00002"])

    def test_other_filter_asks_source_again(self):
        self.cached.search([KEYWORD], 2)
        self.cached.search([KEYWORD], 2, SearchFilter(peer_reviewed_only=True))
        self.assertEqual(self.inner.calls, 2)

    def test_save_failure_still_returns_documents(self):
        calls = []

        def connect_once():
            calls.append(1)
            if len(calls) > 1:
                raise StorageError("gone")
            return connect(TEST_DATABASE_URL)

        cached = CachedSource(self.inner, connect=connect_once)
        documents = cached.search([KEYWORD], 2)
        self.assertEqual(len(documents), 2)
        self.assertEqual(cached.notes, (CACHE_UNAVAILABLE,))

    def test_notes_reset_between_calls(self):
        self.cached.search([KEYWORD], 2)
        self.cached.search([KEYWORD], 2)
        self.cached.search([KEYWORD, "neu"], 2)
        self.assertEqual(self.cached.notes, ())

    def test_source_without_documents_is_no_cache_error(self):
        cached = CachedSource(FakeSource([]), connect=lambda: connect(TEST_DATABASE_URL))
        self.assertEqual(cached.search([KEYWORD], 2), [])
        self.assertEqual(cached.notes, ())
