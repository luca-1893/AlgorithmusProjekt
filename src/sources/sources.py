import re
import urllib.request
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from datetime import date
from typing import Callable, Optional
from urllib.parse import urlencode

from .fulltext import FullTextFetcher

ARXIV_API_URL = "https://export.arxiv.org/api/query"
ARXIV_ERROR_PREFIX = "https://arxiv.org/api/errors"
ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"
USER_AGENT = "AlgorithmusProjekt/0.1"
PEER_REVIEW_OVERFETCH = 3
ORIGINS = ("html", "pdf", "abstract")


class SourceError(Exception):
    """Raised when a research source is unreachable or answers with an error."""


@dataclass(frozen=True)
class Document:
    """A research document with the metadata needed for ranking and citation."""
    id: str
    title: str
    abstract: str
    authors: tuple[str, ...]
    published: date
    url: str
    source: str
    categories: tuple[str, ...] = ()
    journal_ref: str = ""
    doi: str = ""
    origin: str = "abstract"
    full_text: str = ""

    def __post_init__(self):
        if self.origin not in ORIGINS:
            raise ValueError(f"origin must be one of {ORIGINS}")
        if (self.origin == "abstract") != (not self.full_text):
            raise ValueError("full_text must be empty exactly when origin is 'abstract'")

    def abstract_only(self) -> "Document":
        """The same document without full text (C15)."""
        return replace(self, origin="abstract", full_text="")

    @property
    def peer_reviewed(self) -> bool:
        """True if the paper has a journal reference or DOI, i.e. was published beyond the preprint."""
        return bool(self.journal_ref or self.doi)

    @property
    def text(self) -> str:
        """Title and full text, otherwise title and abstract, separated by a blank line (R17)."""
        body = self.full_text or self.abstract
        return f"{self.title}\n\n{body}" if body else self.title


@dataclass(frozen=True)
class SearchFilter:
    """Restricts a search; empty fields mean no restriction."""
    published_from: Optional[date] = None
    published_to: Optional[date] = None
    categories: tuple[str, ...] = ()
    peer_reviewed_only: bool = False

    def __post_init__(self):
        if self.published_from and self.published_to and self.published_from > self.published_to:
            raise ValueError("published_from must not be after published_to")


def normalize_keywords(keywords: list[str]) -> list[str]:
    """Strips and collapses whitespace, drops empty keywords and case-insensitive duplicates."""
    result = []
    seen = set()
    for keyword in keywords:
        cleaned = " ".join(keyword.split())
        key = cleaned.casefold()
        if cleaned and key not in seen:
            result.append(cleaned)
            seen.add(key)
    return result


def build_arxiv_url(keywords: list[str], max_results: int, categories: tuple[str, ...] = (),
                    published_from: Optional[date] = None, published_to: Optional[date] = None) -> str:
    """Builds the arXiv query URL; keywords are OR-combined, categories and dates restrict the search."""
    if not keywords:
        raise ValueError("keywords must not be empty")
    if max_results <= 0:
        raise ValueError("max_results must be > 0")

    unquoted = [keyword.replace('"', "") for keyword in keywords]
    query = " OR ".join(f'all:"{keyword}"' for keyword in unquoted)
    if categories:
        category_filter = " OR ".join(f"cat:{category}" for category in categories)
        query = f"({query}) AND ({category_filter})"
    if published_from or published_to:
        start = (published_from or date(1991, 1, 1)).strftime("%Y%m%d")
        end = (published_to or date(9999, 12, 31)).strftime("%Y%m%d")
        query = f"{query} AND submittedDate:[{start}0000 TO {end}2359]"

    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    return f"{ARXIV_API_URL}?{urlencode(params)}"


def parse_arxiv_feed(xml_text: str) -> list[Document]:
    """Parses an arXiv Atom feed into documents; skips incomplete entries."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as error:
        raise SourceError(f"arXiv response is not valid XML: {error}") from error

    documents = []
    for entry in root.iter(f"{ATOM}entry"):
        entry_id = _text(entry, "id")
        if entry_id.startswith(ARXIV_ERROR_PREFIX):
            raise SourceError(f"arXiv reported an error: {_text(entry, 'summary')}")

        title = _text(entry, "title")
        published = _text(entry, "published")
        if not entry_id or not title or not published:
            continue

        documents.append(Document(
            id=re.sub(r"v\d+$", "", entry_id.split("/abs/")[-1]),
            title=title,
            abstract=_text(entry, "summary"),
            authors=tuple(_text(author, "name") for author in entry.iter(f"{ATOM}author")),
            published=date.fromisoformat(published[:10]),
            url=_alternate_link(entry) or entry_id,
            source="arxiv",
            categories=tuple(category.get("term", "") for category in entry.findall(f"{ATOM}category")),
            journal_ref=_text(entry, "journal_ref", ARXIV),
            doi=_text(entry, "doi", ARXIV),
        ))
    return documents


def _text(element: ET.Element, tag: str, namespace: str = ATOM) -> str:
    """Returns the whitespace-normalized text of a child element, or an empty string."""
    child = element.find(f"{namespace}{tag}")
    return " ".join(child.text.split()) if child is not None and child.text else ""


def _alternate_link(entry: ET.Element) -> str:
    """Returns the href of the entry's alternate link, or an empty string."""
    for link in entry.findall(f"{ATOM}link"):
        if link.get("rel") == "alternate":
            return link.get("href", "")
    return ""


def http_get(url: str, timeout: float = 20.0) -> str:
    """Fetches the URL and returns the response body as text."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def http_get_bytes(url: str, timeout: float = 60.0) -> tuple[bytes, str]:
    """Fetches the URL and returns the raw body and its content type, for HTML and PDF downloads."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), response.headers.get("Content-Type", "")


class Source(ABC):
    """A research source that finds documents for a list of keywords."""
    name: str
    notes: tuple[str, ...] = ()
    full_text: bool = False

    @abstractmethod
    def search(self, keywords: list[str], max_results: int,
               search_filter: Optional[SearchFilter] = None) -> list[Document]:
        """Returns up to max_results documents for the keywords that pass the filter."""

    def add_full_texts(self, documents: list[Document]) -> list[Document]:
        """Documents with full text where the source can load it; this default source cannot."""
        return list(documents)


class ArxivSource(Source):
    """Searches arXiv, optionally with full texts (R17); fetch and full_texts are injectable for tests."""
    name = "arxiv"

    def __init__(self, categories: tuple[str, ...] = (), fetch: Callable[[str], str] = http_get,
                 full_text: bool = False, full_texts: Optional[FullTextFetcher] = None):
        self.categories = categories
        self.fetch = fetch
        self.full_text = full_text
        self.full_texts = full_texts or FullTextFetcher(http_get_bytes)
        self.notes = ()

    def search(self, keywords: list[str], max_results: int,
               search_filter: Optional[SearchFilter] = None) -> list[Document]:
        """Up to max_results arXiv documents, with full text in full-text mode; arXiv filters dates and categories."""
        search_filter = search_filter or SearchFilter()
        self.notes = ()
        fetch_count = max_results * PEER_REVIEW_OVERFETCH if search_filter.peer_reviewed_only else max_results
        url = build_arxiv_url(normalize_keywords(keywords), fetch_count, search_filter.categories or self.categories,
                              search_filter.published_from, search_filter.published_to)
        if self.full_text:
            self.full_texts.wait()
        try:
            xml_text = self.fetch(url)
        except OSError as error:
            raise SourceError(f"arXiv is not reachable: {error}") from error

        documents = parse_arxiv_feed(xml_text)
        if search_filter.peer_reviewed_only:
            documents = [document for document in documents if document.peer_reviewed]
        documents = documents[:max_results]
        return self.add_full_texts(documents) if self.full_text else documents

    def add_full_texts(self, documents: list[Document]) -> list[Document]:
        """Documents with the HTML or PDF text, the rest keeps its abstract with a warning in notes (R17)."""
        documents, self.notes = self.full_texts.add_full_texts(documents)
        return documents
