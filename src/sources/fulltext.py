"""Full text of arXiv papers: HTML version first, PDF second, abstract as fallback (R17, ADR 0006)."""
import http.client
import io
import logging
import re
import time
from dataclasses import replace
from html.parser import HTMLParser
from typing import Callable, Optional
from urllib.error import HTTPError

ARXIV_HTML_URL = "https://export.arxiv.org/html/{}"
ARXIV_PDF_URL = "https://export.arxiv.org/pdf/{}"
MIN_WORDS = 500
PAUSE_S = 3.1
MAX_ATTEMPTS = 4
FIRST_BACKOFF_S = 5.0
RETRY_STATUS = (429, 503)
ARXIV_THROTTLED = "arXiv drosselt (HTTP 429), weitere Volltexte übersprungen"

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
SKIP_TAGS = {"script", "style", "math", "nav", "header", "footer", "svg", "figure", "table"}
SKIP_CLASSES = {"ltx_bibliography", "ltx_page_footer", "ltx_page_header", "ltx_authors", "ltx_role_footnote", "ltx_pubnotes"}
BLOCK_TAGS = {"p", "div", "section", "h1", "h2", "h3", "h4", "li"}
REFERENCES_HEADING = re.compile(r"^[ \t]*(?:\d+\.?[ \t]*)?(?:References|REFERENCES|Bibliography|BIBLIOGRAPHY)[ \t]*$",
                                re.MULTILINE)

Fetch = Callable[[str], tuple[bytes, str]]


class PdfError(Exception):
    """Raised when a PDF cannot be read or pypdf is missing."""


class _ArticleText(HTMLParser):
    """Collects the text inside <article>, without formulas, tables, figures and bibliography."""

    def __init__(self):
        super().__init__()
        self.in_article = 0
        self.skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in VOID_TAGS:
            if tag == "br" and self.in_article and not self.skip:
                self.parts.append(" ")
            return
        if self.skip:
            self.skip += 1
            return
        if tag == "article":
            self.in_article += 1
        css_classes = set((dict(attrs).get("class") or "").split())
        if self.in_article and (tag in SKIP_TAGS or css_classes & SKIP_CLASSES):
            self.skip = 1

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        if self.skip:
            self.skip -= 1
            return
        if tag == "article":
            self.in_article -= 1
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if self.in_article and not self.skip:
            self.parts.append(data)


def html_text(html: str) -> str:
    """Text of the <article> element with whitespace collapsed; empty if the page has no article."""
    parser = _ArticleText()
    parser.feed(html)
    parser.close()
    return collapse_text("".join(parser.parts))


def collapse_text(text: str) -> str:
    """Text without NUL characters (PostgreSQL rejects them) and with whitespace collapsed to single spaces."""
    return " ".join(text.replace("\x00", "").split())


def cut_references(text: str) -> str:
    """Text before the last References/Bibliography heading, if that heading is in the second half."""
    headings = list(REFERENCES_HEADING.finditer(text))
    if headings and headings[-1].start() > len(text) * 0.5:
        return text[:headings[-1].start()]
    return text


def pdf_text(data: bytes) -> str:
    """Text of all pages via pypdf, without bibliography and end-of-line hyphens, whitespace collapsed."""
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    try:
        from pypdf import PdfReader
        text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages)
    except Exception as error:
        raise PdfError(f"PDF not readable: {error}") from error
    return collapse_text(re.sub(r"(\w)-\n(\w)", r"\1\2", cut_references(text)))


def word_count(text: str) -> int:
    """Number of whitespace-separated words."""
    return len(text.split())


class FullTextFetcher:
    """Loads full texts one request after another, with a pause and growing waits on HTTP 429 (R17)."""

    def __init__(self, fetch: Fetch, sleep: Callable[[float], None] = time.sleep,
                 clock: Callable[[], float] = time.monotonic, pause_s: float = PAUSE_S,
                 max_attempts: int = MAX_ATTEMPTS, first_backoff_s: float = FIRST_BACKOFF_S,
                 extract_pdf: Callable[[bytes], str] = pdf_text):
        self.fetch = fetch
        self.sleep = sleep
        self.clock = clock
        self.pause_s = pause_s
        self.max_attempts = max_attempts
        self.first_backoff_s = first_backoff_s
        self.extract_pdf = extract_pdf
        self.throttled = False
        self._last_request: Optional[float] = None

    def wait(self) -> None:
        """Sleeps until pause_s has passed since the previous request and marks a new request."""
        if self._last_request is not None:
            remaining = self.pause_s - (self.clock() - self._last_request)
            if remaining > 0:
                self.sleep(remaining)
        self._last_request = self.clock()

    def get(self, url: str) -> Optional[tuple[bytes, str]]:
        """Body and content type, or None on any failure; 429 and 503 are retried with doubling waits."""
        for attempt in range(1, self.max_attempts + 1):
            self.wait()
            try:
                return self.fetch(url)
            except HTTPError as error:
                if error.code not in RETRY_STATUS:
                    return None
                if attempt < self.max_attempts:
                    self.sleep(self.first_backoff_s * 2 ** (attempt - 1))
            except (OSError, http.client.HTTPException):
                return None
        self.throttled = True
        return None

    def full_text(self, arxiv_id: str) -> Optional[tuple[str, str]]:
        """(origin, text) from the HTML version, otherwise from the PDF, or None if neither is usable."""
        response = self.get(ARXIV_HTML_URL.format(arxiv_id))
        if response and "html" in response[1]:
            text = html_text(response[0].decode("utf-8", "replace"))
            if word_count(text) >= MIN_WORDS:
                return "html", text
        if self.throttled:
            return None
        response = self.get(ARXIV_PDF_URL.format(arxiv_id))
        if not response or not response[0].startswith(b"%PDF"):
            return None
        try:
            text = self.extract_pdf(response[0])
        except PdfError:
            return None
        return ("pdf", text) if word_count(text) >= MIN_WORDS else None

    def add_full_texts(self, documents: list) -> tuple[list, tuple[str, ...]]:
        """Documents with full text where available, in the same order, and the warnings for the rest."""
        self.throttled = False
        result, missing = [], []
        for document in documents:
            found = None if self.throttled else self.full_text(document.id)
            if found is None:
                result.append(document)
                missing.append(document.id)
            else:
                result.append(replace(document, origin=found[0], full_text=found[1]))
        notes = []
        if missing:
            notes.append(f"Volltext nicht verfügbar für {len(missing)} von {len(documents)} Dokumenten, "
                         f"dort nur Titel und Abstract: {', '.join(missing)}")
        if self.throttled:
            notes.append(ARXIV_THROTTLED)
        return result, tuple(notes)
