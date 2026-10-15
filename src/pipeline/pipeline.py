from dataclasses import dataclass
from typing import Optional

from bm25 import build_index, top_m
from chunking import Chunk, create_chunks
from ranking import normalize_scores, reciprocal_rank_fusion
from sources import Document, Source, normalize_keywords
from vector_search import Embedder, EmbeddingError, mmr_select, most_similar


@dataclass(frozen=True)
class PipelineConfig:
    """Tuning parameters of the research pipeline."""
    max_documents: int = 20
    chunk_size: int = 200
    overlap: int = 40
    candidates_m: int = 50
    k_rrf: int = 60
    mmr_lambda: float = 0.7


@dataclass(frozen=True)
class Hit:
    """One selected chunk together with its document and score."""
    document: Document
    chunk: Chunk
    score: float

    def to_dict(self) -> dict:
        """JSON-ready representation for the MCP tool."""
        return {
            "document_id": self.document.id,
            "title": self.document.title,
            "authors": list(self.document.authors),
            "published": self.document.published.isoformat(),
            "url": self.document.url,
            "source": self.document.source,
            "chunk_position": self.chunk.position,
            "text": self.chunk.text,
            "score": self.score,
        }


@dataclass(frozen=True)
class ResearchResult:
    """Selected hits, best first, and notes about empty results or fallbacks."""
    hits: tuple[Hit, ...]
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        """JSON-ready representation for the MCP tool."""
        return {"hits": [hit.to_dict() for hit in self.hits], "warnings": list(self.warnings)}


def research(keywords: list[str], k: int, source: Source, embedder: Optional[Embedder] = None,
             question: str = "", config: PipelineConfig = PipelineConfig()) -> ResearchResult:
    """Finds documents for the keywords and returns the k best chunks."""
    if k <= 0:
        raise ValueError("k must be > 0")
    keywords = normalize_keywords(keywords)
    if not keywords:
        raise ValueError("keywords must not be empty")

    documents = source.search(keywords, config.max_documents)
    if not documents:
        return ResearchResult((), ("Keine Treffer",))

    chunks = [(chunk, document)
              for document in documents
              for chunk in create_chunks(document.id, document.text, config.chunk_size, config.overlap)]
    if not chunks:
        return ResearchResult((), ("Keine verwertbaren Quellen",))

    index, doc_lengths, n_docs, avgdl = build_index([chunk.text for chunk, _ in chunks])
    bm25_hits = top_m(" ".join(keywords), index, doc_lengths, n_docs, avgdl, config.candidates_m)

    if embedder is None:
        return _bm25_only(bm25_hits, chunks, k)
    query = question.strip() or " ".join(keywords)
    return _hybrid(bm25_hits, chunks, k, embedder, query, config)


def _bm25_only(bm25_hits: list[tuple[int, float]], chunks: list[tuple[Chunk, Document]], k: int) -> ResearchResult:
    """Takes the k best BM25 hits as the result."""
    if not bm25_hits:
        return ResearchResult((), ("Kein Chunk enthält ein Schlagwort",))
    return ResearchResult(tuple(Hit(chunks[position][1], chunks[position][0], score)
                                for position, score in bm25_hits[:k]))


def _hybrid(bm25_hits: list[tuple[int, float]], chunks: list[tuple[Chunk, Document]], k: int,
            embedder: Embedder, query: str, config: PipelineConfig) -> ResearchResult:
    """Fuses BM25 and vector ranking with RRF and picks k diverse chunks with MMR."""
    if bm25_hits:
        candidates = [position for position, _ in bm25_hits]
        bm25_ranking = list(range(len(candidates)))
    else:
        candidates = list(range(len(chunks)))
        bm25_ranking = []

    try:
        vectors = embedder.embed([query] + [chunks[position][0].text for position in candidates])
    except EmbeddingError:
        fallback = _bm25_only(bm25_hits, chunks, k)
        return ResearchResult(fallback.hits, fallback.warnings + ("Vektorsuche nicht verfügbar, nur BM25",))

    query_vector, candidate_vectors = vectors[0], vectors[1:]
    vector_ranking = [local for local, _ in most_similar(query_vector, candidate_vectors, len(candidates))]

    fused = reciprocal_rank_fusion([bm25_ranking, vector_ranking], config.k_rrf)
    relevance = normalize_scores([score for _, score in fused])
    fused_vectors = [candidate_vectors[local] for local, _ in fused]
    selected = mmr_select(relevance, fused_vectors, k, config.mmr_lambda)

    hits = []
    for index in selected:
        local, score = fused[index]
        chunk, document = chunks[candidates[local]]
        hits.append(Hit(document, chunk, score))
    return ResearchResult(tuple(hits))
