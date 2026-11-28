import importlib.util
import logging
import unittest
from datetime import date
from urllib.error import HTTPError, URLError

import sources
from sources.fulltext import (ARXIV_THROTTLED, MIN_WORDS, FullTextFetcher, PdfError, collapse_text, cut_references,
                              html_text, pdf_text)

HAS_PYPDF = importlib.util.find_spec("pypdf") is not None
LONG_BODY = " ".join(f"word{number}" for number in range(MIN_WORDS))
HTML_PAGE = f"""<html><head><title>Paper</title><style>p {{ color: red; }}</style></head><body>
<nav>Navigation</nav>
<article class="ltx_document">
  <h1 class="ltx_title">A Paper</h1>
  <div class="ltx_authors">Ada Lovelace</div>
  <section><p>Intro text with BM25.<br>Second line.</p>
  <math><mi>x</mi></math>
  <figure><img src="a.png"><figcaption>Figure text</figcaption></figure>
  <table><tr><td>cell</td></tr></table>
  <p>{LONG_BODY}</p></section>
  <section class="ltx_bibliography"><p>[1] Some reference</p></section>
</article>
<footer>Footer</footer>
</body></html>"""
SHORT_HTML = "<html><body><article><p>Conversion failed.</p></article></body></html>"


def make_pdf(lines):
    """A minimal valid PDF with one page that shows the lines in Helvetica."""
    content = "BT /F1 12 Tf 72 720 Td 14 TL " + " ".join(f"({line}) Tj T*" for line in lines) + " ET"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> "
        "/Contents 4 0 R >>",
        f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    body = b"%PDF-1.4\n"
    offsets = []
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(body))
        body += f"{number} 0 obj\n{obj}\nendobj\n".encode("latin-1")
    xref = len(body)
    body += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("latin-1")
    body += "".join(f"{offset:010d} 00000 n \n" for offset in offsets).encode("latin-1")
    body += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("latin-1")
    return body


def too_many_requests(url):
    return HTTPError(url, 429, "Too Many Requests", {}, None)


def not_found(url):
    return HTTPError(url, 404, "Not Found", {}, None)


class FakeClock:
    """Time that only moves when sleep is called."""

    def __init__(self):
        self.now = 1000.0
        self.sleeps = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


class FakeBytesFetch:
    """Answers per URL suffix with a list of responses; an exception in the list is raised."""

    def __init__(self, responses):
        self.responses = {suffix: list(answers) for suffix, answers in responses.items()}
        self.urls = []

    def __call__(self, url):
        self.urls.append(url)
        kind = "html" if "/html/" in url else "pdf"
        answers = self.responses.get(kind, [])
        answer = answers.pop(0) if len(answers) > 1 else (answers[0] if answers else not_found(url))
        if isinstance(answer, Exception):
            raise answer
        return answer


def fetcher(responses, extract_pdf=None, clock=None):
    clock = clock or FakeClock()
    return FullTextFetcher(FakeBytesFetch(responses), sleep=clock.sleep, clock=clock,
                           extract_pdf=extract_pdf or (lambda data: data.decode("latin-1").removeprefix("%PDF-1.4 ")))


def html(text=HTML_PAGE):
    return text.encode("utf-8"), "text/html; charset=utf-8"


def pdf(text=LONG_BODY):
    return b"%PDF-1.4 " + text.encode("latin-1"), "application/pdf"


def document(number=1):
    return sources.Document(f"2401.{number:05d}", f"Title {number}", f"Abstract {number}", ("Ada",),
                            date(2024, 1, 1), f"https://arxiv.org/abs/2401.{number:05d}", "arxiv")


class TestHtmlText(unittest.TestCase):
    def test_html_keeps_article_text(self):
        text = html_text(HTML_PAGE)
        self.assertTrue(text.startswith("A Paper Intro text with BM25. Second line."))
        self.assertIn(LONG_BODY, text)

    def test_html_skips_math_figures_tables_and_bibliography(self):
        text = html_text(HTML_PAGE)
        for unwanted in ("Ada Lovelace", "Figure text", "cell", "Some reference", "x"):
            self.assertNotIn(f" {unwanted} ", f" {text} ")

    def test_html_outside_article_is_ignored(self):
        text = html_text(HTML_PAGE)
        for unwanted in ("Navigation", "Footer", "color", "Paper A"):
            self.assertNotIn(unwanted, text)

    def test_html_skip_class_must_match_whole_class_name(self):
        page = '<article class="ltx_document ltx_authors_1line"><p>kept</p><div class="ltx_authors">Ada</div></article>'
        self.assertEqual(html_text(page), "kept")

    def test_html_without_article_is_empty(self):
        self.assertEqual(html_text("<html><body><p>No article.</p></body></html>"), "")

    def test_html_void_tag_inside_skipped_element_keeps_skipping(self):
        text = html_text("<article><figure><img src='a'><br><p>hidden</p></figure><p>shown</p></article>")
        self.assertEqual(text, "shown")


class TestCollapseText(unittest.TestCase):
    def test_collapse_removes_nul_characters(self):
        self.assertEqual(collapse_text("classi\x00fication  of\n\tterms"), "classification of terms")

    def test_collapse_empty_text(self):
        self.assertEqual(collapse_text(" \n "), "")


class TestCutReferences(unittest.TestCase):
    def test_cut_references_in_second_half(self):
        text = "Intro\n" + "body " * 50 + "\nReferences\n[1] A. Author."
        self.assertNotIn("A. Author", cut_references(text))

    def test_cut_references_heading_in_first_half_is_kept(self):
        text = "Intro\nReferences\n" + "body " * 50
        self.assertEqual(cut_references(text), text)

    def test_cut_references_without_heading_unchanged(self):
        self.assertEqual(cut_references("just text"), "just text")

    def test_cut_references_uses_last_heading(self):
        text = "Intro " * 10 + "\nBibliography\n" + "body " * 50 + "\nREFERENCES\n[1] Late."
        self.assertEqual(cut_references(text).count("body"), 50)


@unittest.skipUnless(HAS_PYPDF, "pypdf missing, use .venv")
class TestPdfText(unittest.TestCase):
    def test_pdf_text_extracts_words(self):
        self.assertEqual(pdf_text(make_pdf(["Hello BM25 world"])), "Hello BM25 world")

    def test_pdf_text_joins_hyphenated_words(self):
        self.assertEqual(pdf_text(make_pdf(["Algo-", "rithmus"])), "Algorithmus")

    def test_pdf_text_invalid_bytes_raise_pdf_error(self):
        logging.getLogger("pypdf").setLevel(logging.CRITICAL)
        self.addCleanup(logging.getLogger("pypdf").setLevel, logging.NOTSET)
        with self.assertRaises(PdfError):
            pdf_text(b"%PDF-1.4 broken")


class TestFullTextFetcher(unittest.TestCase):
    def test_html_is_preferred(self):
        source = fetcher({"html": [html()], "pdf": [pdf()]})
        origin, text = source.full_text("2401.00001")
        self.assertEqual(origin, "html")
        self.assertIn(LONG_BODY, text)
        self.assertEqual(source.fetch.urls, ["https://export.arxiv.org/html/2401.00001"])

    def test_pdf_fallback_when_html_missing(self):
        source = fetcher({"html": [not_found("u")], "pdf": [pdf()]})
        self.assertEqual(source.full_text("2401.00001"), ("pdf", LONG_BODY))
        self.assertEqual(source.fetch.urls[-1], "https://export.arxiv.org/pdf/2401.00001")

    def test_pdf_fallback_when_html_too_short(self):
        source = fetcher({"html": [html(SHORT_HTML)], "pdf": [pdf()]})
        self.assertEqual(source.full_text("2401.00001")[0], "pdf")

    def test_pdf_fallback_when_html_is_not_html(self):
        source = fetcher({"html": [(b"{}", "application/json")], "pdf": [pdf()]})
        self.assertEqual(source.full_text("2401.00001")[0], "pdf")

    def test_none_when_html_and_pdf_fail(self):
        self.assertIsNone(fetcher({"html": [not_found("u")], "pdf": [not_found("u")]}).full_text("2401.00001"))

    def test_none_when_pdf_too_short(self):
        self.assertIsNone(fetcher({"pdf": [pdf("few words")]}).full_text("2401.00001"))

    def test_none_when_pdf_is_not_a_pdf(self):
        self.assertIsNone(fetcher({"pdf": [(b"<html>", "text/html")]}).full_text("2401.00001"))

    def test_none_when_pdf_unreadable(self):
        def broken(data):
            raise PdfError("broken")
        self.assertIsNone(fetcher({"pdf": [pdf()]}, extract_pdf=broken).full_text("2401.00001"))

    def test_network_error_is_not_retried(self):
        source = fetcher({"html": [URLError("down")], "pdf": [TimeoutError()]})
        self.assertIsNone(source.full_text("2401.00001"))
        self.assertEqual(len(source.fetch.urls), 2)
        self.assertFalse(source.throttled)

    def test_retry_after_429_with_growing_wait(self):
        clock = FakeClock()
        source = fetcher({"html": [too_many_requests("u"), too_many_requests("u"), html()]}, clock=clock)
        self.assertEqual(source.full_text("2401.00001")[0], "html")
        self.assertEqual(len(source.fetch.urls), 3)
        self.assertEqual([wait for wait in clock.sleeps if wait >= 5], [5.0, 10.0])
        self.assertFalse(source.throttled)

    def test_503_is_retried_like_429(self):
        source = fetcher({"html": [HTTPError("u", 503, "Unavailable", {}, None), html()]})
        self.assertEqual(source.full_text("2401.00001")[0], "html")

    def test_gives_up_after_max_attempts_and_skips_pdf(self):
        clock = FakeClock()
        source = fetcher({"html": [too_many_requests("u")], "pdf": [pdf()]}, clock=clock)
        self.assertIsNone(source.full_text("2401.00001"))
        self.assertEqual(len(source.fetch.urls), source.max_attempts)
        self.assertEqual([wait for wait in clock.sleeps if wait >= 5], [5.0, 10.0, 20.0])
        self.assertTrue(source.throttled)

    def test_pause_between_requests(self):
        clock = FakeClock()
        source = fetcher({"html": [not_found("u")], "pdf": [pdf()]}, clock=clock)
        source.full_text("2401.00001")
        self.assertEqual(clock.sleeps, [source.pause_s])

    def test_no_pause_after_enough_time(self):
        clock = FakeClock()
        source = fetcher({"html": [html()]}, clock=clock)
        source.full_text("2401.00001")
        clock.now += 10
        source.full_text("2401.00002")
        self.assertEqual(clock.sleeps, [])


class TestAddFullTexts(unittest.TestCase):
    def test_add_full_texts_sets_origin_and_text(self):
        documents, notes = fetcher({"html": [html()]}).add_full_texts([document(1)])
        self.assertEqual(documents[0].origin, "html")
        self.assertTrue(documents[0].text.startswith("Title 1\n\nA Paper"))
        self.assertEqual(notes, ())

    def test_add_full_texts_falls_back_to_abstract_with_warning(self):
        responses = {"html": [html(), not_found("u")], "pdf": [not_found("u")]}
        documents, notes = fetcher(responses).add_full_texts([document(1), document(2)])
        self.assertEqual([d.origin for d in documents], ["html", "abstract"])
        self.assertEqual(documents[1], document(2))
        self.assertEqual(len(notes), 1)
        self.assertIn("1 von 2", notes[0])
        self.assertIn("2401.00002", notes[0])

    def test_add_full_texts_keeps_order(self):
        documents, _ = fetcher({"html": [html()]}).add_full_texts([document(3), document(1), document(2)])
        self.assertEqual([d.id for d in documents], ["2401.00003", "2401.00001", "2401.00002"])

    def test_add_full_texts_stops_after_persistent_429(self):
        source = fetcher({"html": [too_many_requests("u")]})
        documents, notes = source.add_full_texts([document(1), document(2)])
        self.assertEqual([d.origin for d in documents], ["abstract", "abstract"])
        self.assertEqual(len(source.fetch.urls), source.max_attempts)
        self.assertIn(ARXIV_THROTTLED, notes)

    def test_add_full_texts_resets_throttle_per_call(self):
        source = fetcher({"html": [too_many_requests("u")] * 4 + [html()]})
        source.add_full_texts([document(1)])
        documents, notes = source.add_full_texts([document(2)])
        self.assertEqual(documents[0].origin, "html")
        self.assertEqual(notes, ())

    def test_add_full_texts_empty_list(self):
        self.assertEqual(fetcher({}).add_full_texts([]), ([], ()))


class TestArxivSourceFullText(unittest.TestCase):
    FEED = ('<?xml version="1.0" encoding="UTF-8"?><feed xmlns="http://www.w3.org/2005/Atom">'
            "<entry><id>http://arxiv.org/abs/2401.00001v1</id><title>Title 1</title>"
            "<summary>Abstract 1</summary><published>2024-01-01T00:00:00Z</published></entry></feed>")

    def test_full_text_is_off_by_default(self):
        source = sources.ArxivSource(fetch=lambda url: self.FEED)
        self.assertFalse(source.full_text)
        self.assertEqual(source.search(["bm25"], 5)[0].origin, "abstract")

    def test_full_text_on_downloads_and_replaces_text(self):
        full_texts = fetcher({"html": [html()]})
        source = sources.ArxivSource(fetch=lambda url: self.FEED, full_text=True, full_texts=full_texts)
        found = source.search(["bm25"], 5)
        self.assertEqual(found[0].origin, "html")
        self.assertIn(LONG_BODY, found[0].text)
        self.assertEqual(source.notes, ())

    def test_full_text_fallback_note_reaches_source_notes(self):
        full_texts = fetcher({"html": [not_found("u")], "pdf": [not_found("u")]})
        source = sources.ArxivSource(fetch=lambda url: self.FEED, full_text=True, full_texts=full_texts)
        self.assertEqual(source.search(["bm25"], 5)[0].text, "Title 1\n\nAbstract 1")
        self.assertEqual(len(source.notes), 1)

    def test_full_text_search_request_keeps_pause(self):
        clock = FakeClock()
        full_texts = fetcher({"html": [html()]}, clock=clock)
        source = sources.ArxivSource(fetch=lambda url: self.FEED, full_text=True, full_texts=full_texts)
        source.search(["bm25"], 5)
        self.assertEqual(clock.sleeps, [full_texts.pause_s])

    def test_add_full_texts_without_full_text_mode_still_works(self):
        source = sources.ArxivSource(fetch=lambda url: self.FEED, full_texts=fetcher({"html": [html()]}))
        self.assertEqual(source.add_full_texts([document(1)])[0].origin, "html")

    def test_default_source_adds_nothing(self):
        class Plain(sources.Source):
            name = "plain"

            def search(self, keywords, max_results, search_filter=None):
                return []
        self.assertEqual(Plain().add_full_texts([document(1)]), [document(1)])
        self.assertFalse(Plain().full_text)


class TestDocumentFullText(unittest.TestCase):
    def test_document_text_prefers_full_text(self):
        full = sources.Document("x", "Title", "Abstract", (), date(2024, 1, 1), "u", "arxiv",
                                origin="pdf", full_text="Body")
        self.assertEqual(full.text, "Title\n\nBody")

    def test_document_default_origin_is_abstract(self):
        self.assertEqual((document().origin, document().full_text), ("abstract", ""))

    def test_document_full_text_without_origin_fails(self):
        with self.assertRaises(ValueError):
            sources.Document("x", "T", "", (), date(2024, 1, 1), "u", "arxiv", full_text="Body")

    def test_document_origin_without_full_text_fails(self):
        with self.assertRaises(ValueError):
            sources.Document("x", "T", "", (), date(2024, 1, 1), "u", "arxiv", origin="html")

    def test_document_unknown_origin_fails(self):
        with self.assertRaises(ValueError):
            sources.Document("x", "T", "", (), date(2024, 1, 1), "u", "arxiv", origin="latex", full_text="B")

    def test_document_abstract_only_drops_full_text(self):
        full = sources.Document("x", "Title", "Abstract", (), date(2024, 1, 1), "u", "arxiv",
                                origin="html", full_text="Body")
        self.assertEqual(full.abstract_only().text, "Title\n\nAbstract")
        self.assertEqual(full.abstract_only().origin, "abstract")


if __name__ == "__main__":
    unittest.main()
