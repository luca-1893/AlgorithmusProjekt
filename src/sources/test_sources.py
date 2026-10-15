import unittest
from urllib.parse import parse_qs, urlparse

import sources


def query_params(url):
    return {key: values[0] for key, values in parse_qs(urlparse(url).query).items()}


class TestNormalizeKeywords(unittest.TestCase):
    def test_normalize_example(self):
        self.assertEqual(sources.normalize_keywords(["  UML ", "class  diagram"]), ["UML", "class diagram"])

    def test_normalize_drops_empty(self):
        self.assertEqual(sources.normalize_keywords(["", "   ", "uml"]), ["uml"])

    def test_normalize_drops_case_insensitive_duplicates(self):
        self.assertEqual(sources.normalize_keywords(["UML", "uml", "Uml"]), ["UML"])

    def test_normalize_keeps_order(self):
        self.assertEqual(sources.normalize_keywords(["b", "a", "c"]), ["b", "a", "c"])

    def test_normalize_empty_list(self):
        self.assertEqual(sources.normalize_keywords([]), [])


class TestBuildArxivUrl(unittest.TestCase):
    def test_url_base(self):
        url = sources.build_arxiv_url(["uml"], 5)
        self.assertTrue(url.startswith("https://export.arxiv.org/api/query?"))

    def test_url_single_keyword(self):
        params = query_params(sources.build_arxiv_url(["uml"], 5))
        self.assertEqual(params["search_query"], 'all:"uml"')

    def test_url_keywords_or_combined(self):
        params = query_params(sources.build_arxiv_url(["uml", "class diagram"], 5))
        self.assertEqual(params["search_query"], 'all:"uml" OR all:"class diagram"')

    def test_url_with_categories(self):
        params = query_params(sources.build_arxiv_url(["uml"], 5, ("cs.SE", "cs.PL")))
        self.assertEqual(params["search_query"], '(all:"uml") AND (cat:cs.SE OR cat:cs.PL)')

    def test_url_paging_and_sorting(self):
        params = query_params(sources.build_arxiv_url(["uml"], 7))
        self.assertEqual((params["start"], params["max_results"], params["sortBy"], params["sortOrder"]),
                         ("0", "7", "relevance", "descending"))

    def test_url_empty_keywords(self):
        with self.assertRaises(ValueError):
            sources.build_arxiv_url([], 5)

    def test_url_max_results_zero(self):
        with self.assertRaises(ValueError):
            sources.build_arxiv_url(["uml"], 0)
