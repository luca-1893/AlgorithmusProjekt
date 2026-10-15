import heapq
import json
import math
import os
import urllib.request
from abc import ABC, abstractmethod
from typing import Callable
from urllib.error import HTTPError

VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
VOYAGE_DEFAULT_MODEL = "voyage-4"


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Returns the cosine of the angle between a and b; 0.0 if either is a zero vector."""
    if len(a) != len(b) or not a:
        raise ValueError("vectors must have the same, non-zero length")

    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def top_k(scores: list[float], k: int) -> list[tuple[int, float]]:
    """Returns the k highest (position, score) pairs, best first; ties keep the lower position first."""
    if k <= 0:
        raise ValueError("k must be > 0")

    # min-heap of the k best so far; heap[0] is the weakest of them.
    # -position: on equal scores the larger position counts as weaker and is dropped first.
    heap = []
    for position, score in enumerate(scores):
        entry = (score, -position)
        if len(heap) < k:
            heapq.heappush(heap, entry)
        elif entry > heap[0]:
            heapq.heapreplace(heap, entry)

    return [(-negative_position, score) for score, negative_position in sorted(heap, reverse=True)]


def most_similar(query_vector: list[float], candidate_vectors: list[list[float]], k: int) -> list[tuple[int, float]]:
    """Returns the k candidates most similar to the query as (position, similarity), best first."""
    similarities = [cosine_similarity(query_vector, candidate) for candidate in candidate_vectors]
    return top_k(similarities, k)


class EmbeddingError(Exception):
    """Raised when the embedding provider fails or returns invalid vectors."""


class Embedder(ABC):
    """Turns texts into vectors; subclasses implement the provider request."""

    def embed(self, texts: list[str], input_type: str = "document") -> list[list[float]]:
        """Returns one vector per text in the same order; input_type is "query" or "document"."""
        if input_type not in ("query", "document"):
            raise ValueError('input_type must be "query" or "document"')
        if not texts:
            return []

        vectors = self._request(texts, input_type)
        if len(vectors) != len(texts):
            raise EmbeddingError(f"expected {len(texts)} vectors, got {len(vectors)}")
        if not vectors[0] or any(len(vector) != len(vectors[0]) for vector in vectors):
            raise EmbeddingError("vectors must be non-empty and of equal length")
        return vectors

    @abstractmethod
    def _request(self, texts: list[str], input_type: str) -> list[list[float]]:
        """Sends the texts to the provider and returns the raw vectors."""


def http_post_json(url: str, body: dict, headers: dict, timeout: float = 30.0) -> dict:
    """Posts body as JSON and returns the decoded JSON response."""
    request = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json", **headers}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class VoyageEmbedder(Embedder):
    """Embeddings from Voyage AI; the API key comes from VOYAGE_API_KEY unless given."""

    def __init__(self, api_key: str = "", model: str = VOYAGE_DEFAULT_MODEL,
                 post: Callable[[str, dict, dict], dict] = http_post_json):
        self.api_key = api_key or os.environ.get("VOYAGE_API_KEY", "")
        if not self.api_key:
            raise EmbeddingError("VOYAGE_API_KEY is not set")
        self.model = model
        self.post = post

    def _request(self, texts: list[str], input_type: str) -> list[list[float]]:
        """Sends one request for all texts and returns the vectors in input order."""
        body = {"input": texts, "model": self.model, "input_type": input_type}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            response = self.post(VOYAGE_API_URL, body, headers)
        except HTTPError as error:
            raise EmbeddingError(f"Voyage answered with HTTP {error.code}") from error
        except (OSError, ValueError) as error:
            raise EmbeddingError(f"Voyage is not reachable: {error}") from error

        try:
            items = sorted(response["data"], key=lambda item: item["index"])
            return [item["embedding"] for item in items]
        except (KeyError, TypeError) as error:
            raise EmbeddingError("Voyage response has an unexpected format") from error


def mmr_select(relevance: list[float], vectors: list[list[float]], k: int, lambda_: float = 0.7) -> list[int]:
    """Selects up to k positions that are relevant and dissimilar to the ones already selected."""
    if len(relevance) != len(vectors):
        raise ValueError("relevance and vectors must have the same length")
    if k <= 0 or not 0 <= lambda_ <= 1:
        raise ValueError("k must be > 0 and lambda_ between 0 and 1")

    selected = []
    remaining = list(range(len(relevance)))
    max_similarity = [0.0] * len(relevance)

    while remaining and len(selected) < k:
        # MMR = lambda * relevance - (1 - lambda) * similarity to the closest already selected chunk
        best = max(remaining, key=lambda p: (lambda_ * relevance[p] - (1 - lambda_) * max_similarity[p], -p))
        selected.append(best)
        remaining.remove(best)
        # only the new pick can raise a candidate's maximum similarity, so one comparison per candidate suffices
        for position in remaining:
            similarity = cosine_similarity(vectors[position], vectors[best])
            max_similarity[position] = max(max_similarity[position], similarity)

    return selected
