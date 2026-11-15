import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from sources import Document, Source

try:
    from evaluation import messlauf
    from evaluation.messlauf import (DEFAULT_K, Question, ProbeClient, ProbeSource, found_source, load_questions,
                                     measure, research_tool, store)
    from storage.storage import Run, connect
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql:///algorithmusprojekt_test")
QUESTION = "Messlauf-Test: Wie viele Skizzen?"
UML = Document("2608.07036", "Sketches", "Class diagrams and activity diagrams.", ("Ada",), date(2026, 8, 1),
               "https://arxiv.org/abs/2608.07036", "arxiv")


def database_available():
    if not HAS_DEPENDENCIES:
        return False
    try:
        connect(TEST_DATABASE_URL).close()
        return True
    except Exception:
        return False


class FakeSource(Source):
    name = "fake"

    def search(self, keywords, max_results, search_filter=None):
        return [UML]


def message(text="", input_tokens=10, output_tokens=5, cache_read=0, stop_reason="end_turn"):
    usage = SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens,
                            cache_creation_input_tokens=None, cache_read_input_tokens=cache_read)
    content = [SimpleNamespace(type="thinking", thinking="..."), SimpleNamespace(type="text", text=text)]
    return SimpleNamespace(usage=usage, stop_reason=stop_reason, content=content)


class FakeClient:
    def __init__(self, messages, tool_input=None):
        self.messages = messages
        self.tool_input = tool_input
        self.requests = []
        self.tool_results = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(tool_runner=self.tool_runner))

    def tool_runner(self, **request):
        self.requests.append(request)
        if self.tool_input is not None:
            self.tool_results.append(request["tools"][0].call(self.tool_input))
        return iter(self.messages)


def question(expected_id="2608.07036"):
    return Question("F14", QUESTION, "de", expected_id)


@unittest.skipUnless(HAS_DEPENDENCIES, "anthropic or psycopg missing, use .venv")
class TestQuestions(unittest.TestCase):
    def test_load_all_25_questions(self):
        questions = load_questions()
        self.assertEqual([q.number for q in questions], [f"F{n:02d}" for n in range(1, 26)])

    def test_language_mix(self):
        self.assertEqual(sum(q.language == "de" for q in load_questions()), 13)

    def test_ignores_rows_without_arxiv_id(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fragen.md"
            path.write_text("| F01 | | | | |\n| F02 | Frage? | en | 2601.00001 | Abstract |\n", encoding="utf-8")
            self.assertEqual(load_questions(path), [Question("F02", "Frage?", "en", "2601.00001")])

    def test_found_source_with_version(self):
        self.assertTrue(found_source("Quellen: https://arxiv.org/abs/2608.07036v2", "2608.07036"))

    def test_found_source_other_paper(self):
        self.assertFalse(found_source("Quellen: https://arxiv.org/abs/2608.07037", "2608.07036"))

    def test_found_source_prefix_is_not_enough(self):
        self.assertFalse(found_source("arXiv 2608.070361", "2608.07036"))


@unittest.skipUnless(HAS_DEPENDENCIES, "anthropic or psycopg missing, use .venv")
class TestMeasure(unittest.TestCase):
    def test_websearch_uses_server_tool_and_no_keywords(self):
        client = FakeClient([message("Antwort 2608.07036")])
        result = measure(client, question(), "agent_websearch", FakeSource(), None)
        self.assertEqual(client.requests[0]["tools"], [messlauf.WEB_SEARCH])
        self.assertEqual((result.run.keywords, result.run.k), (None, None))
        self.assertTrue(result.found_source)

    def test_tokens_summed_over_steps_including_cache(self):
        client = FakeClient([message(input_tokens=10, output_tokens=5), message("fertig", 20, 7, cache_read=3)])
        run = measure(client, question(), "agent_websearch", FakeSource(), None).run
        self.assertEqual((run.input_tokens, run.output_tokens), (33, 12))

    def test_answer_is_text_of_last_message(self):
        client = FakeClient([message("zwischen"), message("Ende")])
        self.assertEqual(measure(client, question(), "agent_websearch", FakeSource(), None).answer, "Ende")

    def test_duration_from_clock(self):
        ticks = iter([1.0, 3.5])
        run = measure(FakeClient([message()]), question(), "agent_websearch", FakeSource(), None,
                      clock=lambda: next(ticks)).run
        self.assertEqual(run.duration_ms, 2500)

    def test_bm25_records_first_tool_call(self):
        client = FakeClient([message("x")], tool_input={"keywords": ["class", "diagrams"], "k": 3})
        result = measure(client, question(), "bm25", FakeSource(), None)
        self.assertEqual((result.run.keywords, result.run.k), (["class", "diagrams"], 3))
        self.assertEqual(json.loads(client.tool_results[0])["hits"][0]["document_id"], "2608.07036")

    def test_bm25_without_embedder_hybrid_with(self):
        embedder = object()
        with mock.patch.object(messlauf, "research_tool", wraps=research_tool) as tool:
            measure(FakeClient([message()]), question(), "bm25", FakeSource(), embedder)
            measure(FakeClient([message()]), question(), "hybrid", FakeSource(), embedder)
        self.assertEqual([call.args[1] for call in tool.call_args_list], [None, embedder])

    def test_no_tool_call_stores_empty_keywords(self):
        run = measure(FakeClient([message()]), question(), "hybrid", FakeSource(), None).run
        self.assertEqual((run.keywords, run.k), ([], DEFAULT_K))

    def test_same_model_and_system_for_all_variants(self):
        client = FakeClient([message()])
        for variant in messlauf.VARIANTS:
            measure(client, question(), variant, FakeSource(), None, model="m")
        self.assertEqual({(r["model"], r["system"]) for r in client.requests}, {("m", messlauf.SYSTEM)})

    def test_unknown_variant(self):
        with self.assertRaises(ValueError):
            measure(FakeClient([message()]), question(), "agent", FakeSource(), None)

    def test_tool_rejects_k_out_of_range(self):
        tool = research_tool(FakeSource(), None, messlauf.PipelineConfig(), [])
        self.assertIn("error", json.loads(tool.call({"keywords": ["uml"], "k": 0})))


@unittest.skipUnless(database_available(), "test database not reachable")
class TestStoreRuns(unittest.TestCase):
    def setUp(self):
        self.cleanup()

    def tearDown(self):
        self.cleanup()

    def cleanup(self):
        with connect(TEST_DATABASE_URL) as connection:
            connection.execute("DELETE FROM runs WHERE question IN (%s, %s)", (QUESTION, messlauf.PROBE_PREFIX + QUESTION))

    def rows(self):
        with connect(TEST_DATABASE_URL) as connection:
            return connection.execute("SELECT variant, keywords, k, input_tokens, found_source FROM runs "
                                      "WHERE question IN (%s, %s) ORDER BY id",
                                      (QUESTION, messlauf.PROBE_PREFIX + QUESTION)).fetchall()

    def test_store_saves_run_and_rating(self):
        result = measure(FakeClient([message("2608.07036")]), question(), "agent_websearch", FakeSource(), None)
        with connect(TEST_DATABASE_URL) as connection:
            store(connection, result)
        self.assertEqual(self.rows(), [("agent_websearch", None, None, 10, True)])

    def test_store_run_without_tool_call(self):
        result = measure(FakeClient([message()]), question(), "bm25", FakeSource(), None)
        with connect(TEST_DATABASE_URL) as connection:
            store(connection, result)
        self.assertEqual(self.rows(), [("bm25", [], DEFAULT_K, 10, False)])

    def test_probe_run_writes_all_variants(self):
        with tempfile.TemporaryDirectory() as folder, \
                mock.patch.object(messlauf, "LOG_DIR", Path(folder)), \
                mock.patch.object(messlauf, "load_questions", return_value=[question()]), \
                mock.patch.object(messlauf, "connect", lambda: connect(TEST_DATABASE_URL)), \
                mock.patch("builtins.print"):
            messlauf.main(["--probe"])
            log = next(Path(folder).glob("*_messlauf_probe/runs.jsonl")).read_text(encoding="utf-8").splitlines()
        self.assertEqual(self.rows(), [("agent_websearch", None, None, 100, True), ("bm25", ["probe"], 3, 100, True),
                                       ("hybrid", ["probe"], 3, 100, True)])
        self.assertEqual(len(log), 3)
        with connect(TEST_DATABASE_URL) as connection:
            questions = connection.execute("SELECT DISTINCT question FROM runs WHERE question LIKE %s",
                                           ("[Probe] Messlauf-Test%",)).fetchall()
        self.assertEqual(questions, [("[Probe] " + QUESTION,)])

    def test_failed_run_is_not_stored(self):
        with tempfile.TemporaryDirectory() as folder, \
                mock.patch.object(messlauf, "LOG_DIR", Path(folder)), \
                mock.patch.object(messlauf, "load_questions", return_value=[question()]), \
                mock.patch.object(messlauf, "connect", lambda: connect(TEST_DATABASE_URL)), \
                mock.patch.object(messlauf, "ProbeClient", side_effect=RuntimeError("api down")), \
                mock.patch("builtins.print"):
            messlauf.main(["--probe", "--varianten", "bm25"])
        self.assertEqual(self.rows(), [])


@unittest.skipUnless(HAS_DEPENDENCIES, "anthropic or psycopg missing, use .venv")
class TestProbe(unittest.TestCase):
    def test_probe_source_is_offline(self):
        self.assertEqual(ProbeSource().search(["x"], 5), [])

    def test_probe_client_cites_expected_paper(self):
        answer = ProbeClient("2601.11143").tool_runner(tools=[{}], messages=[])[0].content[0].text
        self.assertTrue(found_source(answer, "2601.11143"))
