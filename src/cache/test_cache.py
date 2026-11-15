import importlib.util
import os
import unittest
from datetime import date

from sources import Document, SearchFilter, Source, SourceError
from vector_search import Embedder

HAS_PSYCOPG = importlib.util.find_spec("psycopg") is not None
if HAS_PSYCOPG:
    from cache.cache import CACHE_HIT, CACHE_UNAVAILABLE, CachedEmbedder, CachedSource
    from storage.storage import StorageError, connect, find_chunks, save_chunks, save_document

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


class CountingEmbedder(Embedder):
    def __init__(self):
        self.calls = []

    def _request(self, texts, input_type):
        self.calls.append((list(texts), input_type))
        return [[float(len(text)), 1.0] for text in texts]


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


@unittest.skipUnless(HAS_PSYCOPG, "psycopg missing, use .venv")
class TestCachedEmbedderWithoutDatabase(unittest.TestCase):
    def test_is_an_embedder(self):
        self.assertIsInstance(CachedEmbedder(CountingEmbedder(), "m", connect=unreachable), Embedder)

    def test_query_is_never_cached(self):
        inner = CountingEmbedder()
        cached = CachedEmbedder(inner, "m", connect=unreachable)
        self.assertEqual(cached.embed(["frage"], "query"), [[5.0, 1.0]])
        self.assertEqual(inner.calls, [(["frage"], "query")])
        self.assertEqual(cached.notes, ())

    def test_database_unreachable_falls_back(self):
        inner = CountingEmbedder()
        cached = CachedEmbedder(inner, "m", connect=unreachable)
        self.assertEqual(cached.embed(["ab", "abc"]), [[2.0, 1.0], [3.0, 1.0]])
        self.assertEqual(cached.notes, (CACHE_UNAVAILABLE,))


@unittest.skipUnless(database_available(), "test database not reachable")
class TestCachedEmbedderWithDatabase(unittest.TestCase):
    MODEL = "testmodell"

    def setUp(self):
        self.cleanup()
        with connect(TEST_DATABASE_URL) as connection:
            self.document_id = save_document(connection, make_document(1), 200, 40)
            save_chunks(connection, self.document_id, ["eins zwei", "drei vier", "fünf"])
        self.inner = CountingEmbedder()
        self.cached = CachedEmbedder(self.inner, self.MODEL, connect=lambda: connect(TEST_DATABASE_URL))

    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        with connect(TEST_DATABASE_URL) as connection:
            connection.execute("DELETE FROM documents WHERE source = %s", (TEST_SOURCE,))

    def stored_count(self):
        with connect(TEST_DATABASE_URL) as connection:
            return connection.execute("SELECT count(*) FROM chunk_embeddings WHERE model = %s",
                                      (self.MODEL,)).fetchone()[0]

    def test_miss_embeds_and_stores(self):
        vectors = self.cached.embed(["eins zwei", "drei vier"])
        self.assertEqual(vectors, [[9.0, 1.0], [9.0, 1.0]])
        self.assertEqual(self.inner.calls, [(["eins zwei", "drei vier"], "document")])
        self.assertEqual(self.stored_count(), 2)
        self.assertEqual(self.cached.notes, ())

    def test_hit_skips_inner_embedder(self):
        first = self.cached.embed(["eins zwei", "drei vier"])
        second = self.cached.embed(["drei vier", "eins zwei"])
        self.assertEqual(len(self.inner.calls), 1)
        self.assertEqual(second, [first[1], first[0]])

    def test_only_missing_texts_are_embedded(self):
        self.cached.embed(["eins zwei"])
        self.cached.embed(["eins zwei", "fünf"])
        self.assertEqual(self.inner.calls[1], (["fünf"], "document"))

    def test_duplicate_texts_embedded_once(self):
        vectors = self.cached.embed(["fünf", "fünf"])
        self.assertEqual(self.inner.calls, [(["fünf"], "document")])
        self.assertEqual(vectors, [[4.0, 1.0], [4.0, 1.0]])

    def test_text_without_chunk_is_returned_not_stored(self):
        self.assertEqual(self.cached.embed(["gibt es nicht"]), [[13.0, 1.0]])
        self.assertEqual(self.stored_count(), 0)

    def test_save_failure_still_returns_vectors(self):
        connections = iter([connect(TEST_DATABASE_URL)])
        cached = CachedEmbedder(self.inner, self.MODEL, connect=lambda: next(connections, None) or unreachable())
        self.assertEqual(cached.embed(["fünf"]), [[4.0, 1.0]])
        self.assertEqual(cached.notes, (CACHE_UNAVAILABLE,))
        self.assertEqual(self.stored_count(), 0)

    def test_other_model_is_a_miss(self):
        self.cached.embed(["eins zwei"])
        other = CachedEmbedder(self.inner, "anderes", connect=lambda: connect(TEST_DATABASE_URL))
        other.embed(["eins zwei"])
        self.assertEqual(len(self.inner.calls), 2)
        with connect(TEST_DATABASE_URL) as connection:
            connection.execute("DELETE FROM chunk_embeddings WHERE model = 'anderes'")


@unittest.skipUnless(database_available(), "test database not reachable")
class TestCachedSourceStoresChunks(unittest.TestCase):
    def setUp(self):
        self.cleanup()
        self.cached = CachedSource(FakeSource([make_document(1)]), connect=lambda: connect(TEST_DATABASE_URL),
                                   chunk_size=2, overlap=0)

    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        with connect(TEST_DATABASE_URL) as connection:
            connection.execute("DELETE FROM searches WHERE %s = ANY(keywords)", (KEYWORD,))
            connection.execute("DELETE FROM documents WHERE source = %s", (TEST_SOURCE,))

    def document_id(self, connection):
        return connection.execute("SELECT id FROM documents WHERE source = %s", (TEST_SOURCE,)).fetchone()[0]

    def test_chunks_are_stored(self):
        self.cached.search([KEYWORD], 1)
        with connect(TEST_DATABASE_URL) as connection:
            texts = [text for _, _, text in find_chunks(connection, [self.document_id(connection)])]
        self.assertEqual(texts, ["Titel 1", "Abstract 1"])

    def test_storing_again_keeps_embeddings(self):
        self.cached.search([KEYWORD], 1)
        CachedEmbedder(CountingEmbedder(), "testmodell", connect=lambda: connect(TEST_DATABASE_URL)).embed(["Titel 1"])
        self.cached.search([KEYWORD, "andere suche"], 1)
        with connect(TEST_DATABASE_URL) as connection:
            count = connection.execute("SELECT count(*) FROM chunk_embeddings WHERE model = 'testmodell'").fetchone()[0]
        self.assertEqual(count, 1)
