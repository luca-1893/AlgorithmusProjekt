import importlib.util
import unittest
from datetime import date
from unittest import mock

from sources import Document, Source, SourceError
from vector_search import Embedder

HAS_FASTMCP = importlib.util.find_spec("fastmcp") is not None
if HAS_FASTMCP:
    from fastmcp import Client

    from mcp_server.mcp_server import MAX_K, build_server, default_embedder

UML = Document("1", "UML class diagrams", "Class diagrams describe classes in UML.",
               ("Ada",), date(2020, 1, 1), "https://arxiv.org/abs/1", "arxiv")
MANY = [Document(str(i), f"UML paper {i}", "UML diagrams " * (i + 1), ("Bob",), date(2021, 1, 1), f"u{i}", "arxiv")
        for i in range(10)]


class FakeSource(Source):
    name = "fake"

    def __init__(self, documents=(), error=None):
        self.documents = list(documents)
        self.error = error

    def search(self, keywords, max_results):
        if self.error:
            raise self.error
        return self.documents[:max_results]


class RecordingEmbedder(Embedder):
    def __init__(self):
        self.calls = []

    def _request(self, texts, input_type):
        self.calls.append((texts, input_type))
        return [[1.0, float(len(text) % 7)] for text in texts]


@unittest.skipUnless(HAS_FASTMCP, "fastmcp needs Python 3.10 or newer, use .venv")
class TestMcpServer(unittest.IsolatedAsyncioTestCase):
    async def call(self, server, arguments):
        async with Client(server) as client:
            return await client.call_tool("research_papers", arguments, raise_on_error=False)

    async def test_tool_blank_keywords(self):
        result = await self.call(build_server(FakeSource([UML])), {"keywords": ["  "]})
        self.assertTrue(result.is_error)

    async def test_tool_default_k_is_five(self):
        result = await self.call(build_server(FakeSource(MANY)), {"keywords": ["uml"]})
        self.assertEqual(len(result.structured_content["hits"]), 5)

    async def test_tool_is_listed_read_only(self):
        async with Client(build_server(FakeSource())) as client:
            tools = await client.list_tools()
        self.assertEqual([tool.name for tool in tools], ["research_papers"])
        self.assertTrue(tools[0].annotations.read_only_hint)

    async def test_tool_k_too_large(self):
        result = await self.call(build_server(FakeSource([UML])), {"keywords": ["uml"], "k": MAX_K + 1})
        self.assertTrue(result.is_error)

    async def test_tool_k_zero(self):
        result = await self.call(build_server(FakeSource([UML])), {"keywords": ["uml"], "k": 0})
        self.assertTrue(result.is_error)

    async def test_tool_returns_hits(self):
        result = await self.call(build_server(FakeSource([UML])), {"keywords": ["class"], "k": 1})
        hit = result.structured_content["hits"][0]
        self.assertEqual((hit["document_id"], hit["title"], hit["url"]), ("1", "UML class diagrams", "https://arxiv.org/abs/1"))

    async def test_tool_returns_warnings(self):
        result = await self.call(build_server(FakeSource([])), {"keywords": ["uml"]})
        self.assertEqual(result.structured_content, {"hits": [], "warnings": ["Keine Treffer"]})

    async def test_tool_source_error(self):
        result = await self.call(build_server(FakeSource(error=SourceError("down"))), {"keywords": ["uml"]})
        self.assertTrue(result.is_error)
        self.assertIn("not reachable", result.content[0].text)

    async def test_tool_uses_embedder_and_question(self):
        embedder = RecordingEmbedder()
        await self.call(build_server(FakeSource([UML]), embedder), {"keywords": ["uml"], "question": "Was sind Klassendiagramme?"})
        self.assertEqual(embedder.calls[0], (["Was sind Klassendiagramme?"], "query"))


@unittest.skipUnless(HAS_FASTMCP, "fastmcp needs Python 3.10 or newer, use .venv")
class TestDefaultEmbedder(unittest.TestCase):
    def test_default_embedder_with_key(self):
        with mock.patch.dict("os.environ", {"VOYAGE_API_KEY": "key"}):
            self.assertIsNotNone(default_embedder())

    def test_default_embedder_without_key(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertIsNone(default_embedder())
