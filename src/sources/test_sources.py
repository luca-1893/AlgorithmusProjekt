import unittest
from datetime import date
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse

import sources

FEED_HEAD = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">'
)
ENTRY_UML = """
<entry>
  <id>http://arxiv.org/abs/1409.6928v1</id>
  <title>Developing the UML as a
    Formal Modelling Notation</title>
  <link href="https://arxiv.org/abs/1409.6928v1" rel="alternate" type="text/html"/>
  <link href="https://arxiv.org/pdf/1409.6928v1" rel="related" type="application/pdf" title="pdf"/>
  <summary>The Unified Modeling Language (UML) is rapidly
    emerging as a de-facto standard.</summary>
  <published>2014-09-24T12:36:10Z</published>
  <author><name>Andy Evans</name></author>
  <author><name>Robert France</name></author>
</entry>
"""
ENTRY_OLD_ID = """
<entry>
  <id>http://arxiv.org/abs/cs/0112017v2</id>
  <title>An old style identifier</title>
  <summary>Abstract.</summary>
  <published>2001-12-14T00:00:00Z</published>
  <author><name>Jane Doe</name></author>
</entry>
"""
ENTRY_WITHOUT_TITLE = """
<entry>
  <id>http://arxiv.org/abs/2401.00001v1</id>
  <summary>No title.</summary>
  <published>2024-01-01T00:00:00Z</published>
</entry>
"""
ENTRY_ERROR = """
<entry>
  <id>https://arxiv.org/api/errors#start_must_be_non-negative</id>
  <title>Error</title>
  <summary>start must be non-negative</summary>
</entry>
"""


def feed(*entries):
    return FEED_HEAD + "".join(entries) + "</feed>"


def query_params(url):
    return {key: values[0] for key, values in parse_qs(urlparse(url).query).items()}


class TestNormalizeKeywords(unittest.TestCase):
    def test_normalize_does_not_mutate_input(self):
        keywords = ["  UML ", "uml"]
        sources.normalize_keywords(keywords)
        self.assertEqual(keywords, ["  UML ", "uml"])

    def test_normalize_drops_case_insensitive_duplicates(self):
        self.assertEqual(sources.normalize_keywords(["UML", "uml", "Uml"]), ["UML"])

    def test_normalize_drops_empty(self):
        self.assertEqual(sources.normalize_keywords(["", "   ", "uml"]), ["uml"])

    def test_normalize_empty_list(self):
        self.assertEqual(sources.normalize_keywords([]), [])

    def test_normalize_example(self):
        self.assertEqual(sources.normalize_keywords(["  UML ", "class  diagram"]), ["UML", "class diagram"])

    def test_normalize_keeps_order(self):
        self.assertEqual(sources.normalize_keywords(["b", "a", "c"]), ["b", "a", "c"])


class TestBuildArxivUrl(unittest.TestCase):
    def test_url_base(self):
        url = sources.build_arxiv_url(["uml"], 5)
        self.assertTrue(url.startswith("https://export.arxiv.org/api/query?"))

    def test_url_empty_keywords(self):
        with self.assertRaises(ValueError):
            sources.build_arxiv_url([], 5)

    def test_url_keywords_or_combined(self):
        params = query_params(sources.build_arxiv_url(["uml", "class diagram"], 5))
        self.assertEqual(params["search_query"], 'all:"uml" OR all:"class diagram"')

    def test_url_max_results_zero(self):
        with self.assertRaises(ValueError):
            sources.build_arxiv_url(["uml"], 0)

    def test_url_paging_and_sorting(self):
        params = query_params(sources.build_arxiv_url(["uml"], 7))
        self.assertEqual((params["start"], params["max_results"], params["sortBy"], params["sortOrder"]),
                         ("0", "7", "relevance", "descending"))

    def test_url_single_keyword(self):
        params = query_params(sources.build_arxiv_url(["uml"], 5))
        self.assertEqual(params["search_query"], 'all:"uml"')

    def test_url_strips_double_quotes_from_keywords(self):
        params = query_params(sources.build_arxiv_url(['C "Sharp"'], 5))
        self.assertEqual(params["search_query"], 'all:"C Sharp"')

    def test_url_umlauts_round_trip(self):
        params = query_params(sources.build_arxiv_url(["Müller"], 5))
        self.assertEqual(params["search_query"], 'all:"Müller"')

    def test_url_with_categories(self):
        params = query_params(sources.build_arxiv_url(["uml"], 5, ("cs.SE", "cs.PL")))
        self.assertEqual(params["search_query"], '(all:"uml") AND (cat:cs.SE OR cat:cs.PL)')


class TestParseArxivFeed(unittest.TestCase):
    def test_parse_empty_feed(self):
        self.assertEqual(sources.parse_arxiv_feed(feed()), [])

    def test_parse_error_entry(self):
        with self.assertRaises(sources.SourceError):
            sources.parse_arxiv_feed(feed(ENTRY_ERROR))

    def test_parse_example(self):
        self.assertEqual(sources.parse_arxiv_feed(feed(ENTRY_UML)), [sources.Document(
            id="1409.6928",
            title="Developing the UML as a Formal Modelling Notation",
            abstract="The Unified Modeling Language (UML) is rapidly emerging as a de-facto standard.",
            authors=("Andy Evans", "Robert France"),
            published=date(2014, 9, 24),
            url="https://arxiv.org/abs/1409.6928v1",
            source="arxiv",
        )])

    def test_parse_invalid_xml(self):
        with self.assertRaises(sources.SourceError):
            sources.parse_arxiv_feed("<feed><entry>")

    def test_parse_keeps_feed_order(self):
        ids = [document.id for document in sources.parse_arxiv_feed(feed(ENTRY_UML, ENTRY_OLD_ID))]
        self.assertEqual(ids, ["1409.6928", "cs/0112017"])

    def test_parse_old_style_id(self):
        self.assertEqual(sources.parse_arxiv_feed(feed(ENTRY_OLD_ID))[0].id, "cs/0112017")

    def test_parse_skips_incomplete_entry(self):
        ids = [document.id for document in sources.parse_arxiv_feed(feed(ENTRY_WITHOUT_TITLE, ENTRY_UML))]
        self.assertEqual(ids, ["1409.6928"])

    def test_parse_url_falls_back_to_id(self):
        self.assertEqual(sources.parse_arxiv_feed(feed(ENTRY_OLD_ID))[0].url, "http://arxiv.org/abs/cs/0112017v2")


class TestDocument(unittest.TestCase):
    def test_document_is_immutable(self):
        document = sources.Document("x", "Title", "", (), date(2024, 1, 1), "u", "arxiv")
        with self.assertRaises(AttributeError):
            document.title = "anders"

    def test_document_text(self):
        document = sources.parse_arxiv_feed(feed(ENTRY_OLD_ID))[0]
        self.assertEqual(document.text, "An old style identifier\n\nAbstract.")

    def test_document_text_without_abstract(self):
        document = sources.Document("x", "Title", "", (), date(2024, 1, 1), "u", "arxiv")
        self.assertEqual(document.text, "Title")


class FakeFetch:
    def __init__(self, response="", error=None):
        self.response = response
        self.error = error
        self.urls = []

    def __call__(self, url):
        self.urls.append(url)
        if self.error:
            raise self.error
        return self.response


class TestArxivSource(unittest.TestCase):
    def test_arxiv_source_is_a_source(self):
        self.assertIsInstance(sources.ArxivSource(), sources.Source)

    def test_search_blank_keywords_without_fetch(self):
        fetch = FakeFetch(feed())
        with self.assertRaises(ValueError):
            sources.ArxivSource(fetch=fetch).search(["  ", ""], 5)
        self.assertEqual(fetch.urls, [])

    def test_search_fetches_once(self):
        fetch = FakeFetch(feed())
        sources.ArxivSource(fetch=fetch).search(["uml"], 5)
        self.assertEqual(len(fetch.urls), 1)

    def test_search_network_error(self):
        source = sources.ArxivSource(fetch=FakeFetch(error=URLError("no route")))
        with self.assertRaises(sources.SourceError):
            source.search(["uml"], 5)

    def test_search_normalizes_keywords(self):
        fetch = FakeFetch(feed())
        sources.ArxivSource(fetch=fetch).search(["  UML ", "uml"], 5)
        self.assertEqual(query_params(fetch.urls[0])["search_query"], 'all:"UML"')

    def test_search_returns_documents(self):
        source = sources.ArxivSource(fetch=FakeFetch(feed(ENTRY_UML)))
        self.assertEqual([document.id for document in source.search(["uml"], 5)], ["1409.6928"])

    def test_search_timeout(self):
        source = sources.ArxivSource(fetch=FakeFetch(error=TimeoutError()))
        with self.assertRaises(sources.SourceError):
            source.search(["uml"], 5)

    def test_search_uses_categories(self):
        fetch = FakeFetch(feed())
        sources.ArxivSource(categories=("cs.SE",), fetch=fetch).search(["uml"], 5)
        self.assertEqual(query_params(fetch.urls[0])["search_query"], '(all:"uml") AND (cat:cs.SE)')

    def test_source_is_abstract(self):
        with self.assertRaises(TypeError):
            sources.Source()
