from datetime import timedelta
from typing import Callable, Optional

import psycopg

from chunking import create_chunks
from sources import Document, SearchFilter, Source
from storage.storage import (CACHE_MAX_AGE, StorageError, connect, find_cached_search, find_chunks,
                             find_documents, find_embeddings_by_text, save_chunks, save_document,
                             save_embedding_by_text, save_search)
from vector_search import Embedder

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
        self.full_text = inner.full_text
        self.notes = ()

    def search(self, keywords: list[str], max_results: int,
               search_filter: Optional[SearchFilter] = None) -> list[Document]:
        """Documents from a fresh cached search, otherwise from the inner source, which are then stored."""
        search_filter = search_filter or SearchFilter()
        self.notes = ()
        try:
            cached = self._lookup(keywords, max_results, search_filter)
        except StorageError:
            documents = self.inner.search(keywords, max_results, search_filter)
            self.notes = (CACHE_UNAVAILABLE,) + tuple(self.inner.notes)
            return documents
        if cached is not None:
            self.notes = (CACHE_HIT,)
            return self._match_mode(cached)

        documents = self.inner.search(keywords, max_results, search_filter)
        self.notes = tuple(self.inner.notes)
        if not documents:
            return documents
        try:
            self._store(keywords, search_filter, documents)
        except StorageError:
            self.notes = (CACHE_UNAVAILABLE,) + self.notes
        return documents

    def _match_mode(self, cached: list[Document]) -> list[Document]:
        """Cached documents without full text in abstract mode (C15), with missing full texts loaded otherwise (C14)."""
        if not self.full_text:
            return [document.abstract_only() for document in cached]
        abstract_only = [document for document in cached if document.origin == "abstract"]
        if not abstract_only:
            return cached
        completed = {document.id: document for document in self.inner.add_full_texts(abstract_only)}
        self.notes += tuple(self.inner.notes)
        try:
            self._store_documents([document for document in completed.values() if document.full_text])
        except StorageError:
            self.notes += (CACHE_UNAVAILABLE,)
        return [completed.get(document.id, document) for document in cached]

    def _store_documents(self, documents: list[Document]) -> list[int]:
        """Saves the documents with origin, full text and chunks (C8, C10); returns their database ids."""
        ids = []
        with self.connect() as connection:
            for document in documents:
                document_id = save_document(connection, document, self.chunk_size, self.overlap)
                self._store_chunks(connection, document_id, document)
                ids.append(document_id)
        return ids

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
        ids = self._store_documents(documents)
        with self.connect() as connection:
            save_search(connection, keywords, search_filter, ids)

    def _store_chunks(self, connection: psycopg.Connection, document_id: int, document: Document) -> None:
        """Saves the chunks only if their texts changed, so stored vectors survive (C10)."""
        texts = [chunk.text for chunk in create_chunks(document.id, document.text, self.chunk_size, self.overlap)]
        stored = [text for _, _, text in find_chunks(connection, [document_id])]
        if texts and texts != stored:
            save_chunks(connection, document_id, texts)


class CachedEmbedder(Embedder):
    """Reuses stored chunk vectors and asks the inner embedder only for missing ones (R16)."""

    def __init__(self, inner: Embedder, model: str, connect: Callable[[], psycopg.Connection] = connect):
        self.inner = inner
        self.model = model
        self.connect = connect
        self.notes = ()

    def _request(self, texts: list[str], input_type: str) -> list[list[float]]:
        self.notes = ()
        if input_type == "query":
            return self.inner.embed(texts, "query")
        try:
            with self.connect() as connection:
                vectors = find_embeddings_by_text(connection, texts, self.model)
        except StorageError:
            self.notes = (CACHE_UNAVAILABLE,)
            return self.inner.embed(texts, "document")

        missing = list(dict.fromkeys(text for text in texts if text not in vectors))
        new_vectors = self.inner.embed(missing, "document")
        vectors.update(zip(missing, new_vectors))
        try:
            with self.connect() as connection:
                for text, vector in zip(missing, new_vectors):
                    save_embedding_by_text(connection, text, self.model, vector)
        except StorageError:
            self.notes = (CACHE_UNAVAILABLE,)
        return [vectors[text] for text in texts]
