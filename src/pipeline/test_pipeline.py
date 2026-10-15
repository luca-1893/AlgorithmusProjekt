import unittest
from datetime import date

import pipeline
from sources import Document, Source, SourceError

UML = Document("1", "UML class diagrams", "Class diagrams describe classes and associations in UML.",
               ("Ada",), date(2020, 1, 1), "https://arxiv.org/abs/1", "arxiv")
NETS = Document("2", "Neural networks", "Convolutional networks recognise images.",
                ("Bob",), date(2021, 2, 2), "https://arxiv.org/abs/2", "arxiv")
SEQUENCE = Document("3", "UML sequence diagrams", "Sequence diagrams show messages between objects.",
                    ("Cy",), date(2022, 3, 3), "https://arxiv.org/abs/3", "arxiv")


class FakeSource(Source):
    name = "fake"

    def __init__(self, documents=(), error=None):
        self.documents = list(documents)
        self.error = error
        self.calls = []

    def search(self, keywords, max_results):
        self.calls.append((keywords, max_results))
        if self.error:
            raise self.error
        return self.documents[:max_results]


class TestResearchBm25Only(unittest.TestCase):
    def test_research_blank_keywords(self):
        source = FakeSource([UML])
        with self.assertRaises(ValueError):
            pipeline.research(["  ", ""], 3, source)
        self.assertEqual(source.calls, [])

    def test_research_k_zero(self):
        with self.assertRaises(ValueError):
            pipeline.research(["uml"], 0, FakeSource([UML]))

    def test_research_long_document_gives_several_chunks(self):
        config = pipeline.PipelineConfig(chunk_size=4, overlap=1)
        result = pipeline.research(["uml"], 10, FakeSource([UML]), config=config)
        self.assertGreater(len(result.hits), 1)
        self.assertTrue(all(hit.document.id == "1" for hit in result.hits))

    def test_research_matching_document_first(self):
        result = pipeline.research(["class", "diagrams"], 3, FakeSource([NETS, SEQUENCE, UML]))
        self.assertEqual(result.hits[0].document.id, "1")

    def test_research_no_documents(self):
        result = pipeline.research(["uml"], 3, FakeSource([]))
        self.assertEqual((result.hits, result.warnings), ((), ("Keine Treffer",)))

    def test_research_no_keyword_in_chunks(self):
        result = pipeline.research(["quantum"], 3, FakeSource([UML, NETS]))
        self.assertEqual((result.hits, result.warnings), ((), ("Kein Chunk enthält ein Schlagwort",)))

    def test_research_only_matching_documents(self):
        result = pipeline.research(["uml"], 10, FakeSource([UML, NETS, SEQUENCE]))
        self.assertEqual(sorted(hit.document.id for hit in result.hits), ["1", "3"])

    def test_research_passes_normalized_keywords_and_limit(self):
        source = FakeSource([UML])
        pipeline.research([" UML ", "uml", "class"], 3, source, config=pipeline.PipelineConfig(max_documents=7))
        self.assertEqual(source.calls, [(["UML", "class"], 7)])

    def test_research_respects_k(self):
        result = pipeline.research(["uml", "diagrams"], 1, FakeSource([UML, SEQUENCE]))
        self.assertEqual(len(result.hits), 1)

    def test_research_scores_descending(self):
        scores = [hit.score for hit in pipeline.research(["uml", "class"], 10, FakeSource([UML, SEQUENCE])).hits]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_research_source_error_propagates(self):
        with self.assertRaises(SourceError):
            pipeline.research(["uml"], 3, FakeSource(error=SourceError("down")))


class TestResultToDict(unittest.TestCase):
    def test_hit_to_dict(self):
        hit = pipeline.research(["class"], 1, FakeSource([UML])).hits[0]
        self.assertEqual({key: value for key, value in hit.to_dict().items() if key != "score"}, {
            "document_id": "1",
            "title": "UML class diagrams",
            "authors": ["Ada"],
            "published": "2020-01-01",
            "url": "https://arxiv.org/abs/1",
            "source": "arxiv",
            "chunk_position": 0,
            "text": " ".join(UML.text.split()),
        })

    def test_result_to_dict_empty(self):
        self.assertEqual(pipeline.research(["uml"], 3, FakeSource([])).to_dict(),
                         {"hits": [], "warnings": ["Keine Treffer"]})
