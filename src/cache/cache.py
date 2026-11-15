from datetime import timedelta
from typing import Callable, Optional

import psycopg

from sources import Document, SearchFilter, Source
from storage.storage import (CACHE_MAX_AGE, StorageError, connect, find_cached_search, find_documents,
                             save_document, save_search)

CACHE_HIT = "Dokumente aus dem Cache"
CACHE_UNAVAILABLE = "Cache nicht verfügbar"


class CachedSource(Source):
    """Looks up equal searches in the database before asking the inner source (R13 to R15)."""

    def __init__(self, inner: Source, connect: Callable[[], psycopg.Connection] = connect,
                 chunk_size: int = 200, overlap: int = 40, max_age: timedelta = CACHE_MAX_AGE):
        self.inner = inner
        self.name = inner.name
        self.connect = connect
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.max_age = max_age
        self.notes = ()

    def search(self, keywords: list[str], max_results: int,
               search_filter: Optional[SearchFilter] = None) -> list[Document]:
        """Documents from a fresh cached search, otherwise from the inner source, which are then stored."""
        search_filter = search_filter or SearchFilter()
        self.notes = ()
        try:
            cached = self._lookup(keywords, max_results, search_filter)
        except StorageError:
            self.notes = (CACHE_UNAVAILABLE,)
            return self.inner.search(keywords, max_results, search_filter)
        if cached is not None:
            self.notes = (CACHE_HIT,)
            return cached

        documents = self.inner.search(keywords, max_results, search_filter)
        if not documents:
            return documents
        try:
            self._store(keywords, search_filter, documents)
        except StorageError:
            self.notes = (CACHE_UNAVAILABLE,)
        return documents

    def _lookup(self, keywords: list[str], max_results: int,
                search_filter: SearchFilter) -> Optional[list[Document]]:
        """The first max_results documents of a fresh equal search, or None if it has too few (C2)."""
        with self.connect() as connection:
            ids = find_cached_search(connection, keywords, search_filter, self.max_age)
            if len(ids) < max_results:
                return None
            return [entry.document for entry in find_documents(connection, ids[:max_results])]

    def _store(self, keywords: list[str], search_filter: SearchFilter, documents: list[Document]) -> None:
        """Saves the documents and the search in the order of the inner source (R14)."""
        with self.connect() as connection:
            ids = [save_document(connection, document, self.chunk_size, self.overlap) for document in documents]
            save_search(connection, keywords, search_filter, ids)
