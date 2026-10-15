import re
import urllib.request
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Callable
from urllib.parse import urlencode

ARXIV_API_URL = "https://export.arxiv.org/api/query"
ARXIV_ERROR_PREFIX = "https://arxiv.org/api/errors"
ATOM = "{http://www.w3.org/2005/Atom}"
USER_AGENT = "AlgorithmusProjekt/0.1"


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

    @property
    def text(self) -> str:
        """Title and abstract, separated by a blank line."""
        return f"{self.title}\n\n{self.abstract}" if self.abstract else self.title


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


def build_arxiv_url(keywords: list[str], max_results: int, categories: tuple[str, ...] = ()) -> str:
    """Builds the arXiv query URL; keywords are OR-combined, categories restrict the search."""
    if not keywords:
        raise ValueError("keywords must not be empty")
    if max_results <= 0:
        raise ValueError("max_results must be > 0")

    unquoted = [keyword.replace('"', "") for keyword in keywords]
    query = " OR ".join(f'all:"{keyword}"' for keyword in unquoted)
    if categories:
        category_filter = " OR ".join(f"cat:{category}" for category in categories)
        query = f"({query}) AND ({category_filter})"

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
        ))
    return documents


def _text(element: ET.Element, tag: str) -> str:
    """Returns the whitespace-normalized text of a child element, or an empty string."""
    child = element.find(f"{ATOM}{tag}")
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


class Source(ABC):
    """A research source that finds documents for a list of keywords."""
    name: str

    @abstractmethod
    def search(self, keywords: list[str], max_results: int) -> list[Document]:
        """Returns up to max_results documents for the keywords."""


class ArxivSource(Source):
    """Searches arXiv; fetch is injectable so tests run without network."""
    name = "arxiv"

    def __init__(self, categories: tuple[str, ...] = (), fetch: Callable[[str], str] = http_get):
        self.categories = categories
        self.fetch = fetch

    def search(self, keywords: list[str], max_results: int) -> list[Document]:
        """Returns up to max_results arXiv documents for the keywords."""
        url = build_arxiv_url(normalize_keywords(keywords), max_results, self.categories)
        try:
            xml_text = self.fetch(url)
        except OSError as error:
            raise SourceError(f"arXiv is not reachable: {error}") from error
        return parse_arxiv_feed(xml_text)
