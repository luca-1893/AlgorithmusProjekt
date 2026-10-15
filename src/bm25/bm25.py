import heapq
import math

JOINERS = "-'’"

def tokenize(chunk: str) -> list[str]:
    """Normalizes the chunk into a list of casefolded words, stripped of punctuation."""
    folded = chunk.casefold()
    joined = "".join(char for char in folded if char not in JOINERS)
    cleaned = "".join(char if char.isalnum() else " " for char in joined)
    tokens = cleaned.split()
    return tokens


def build_index(corpus: list[str]) -> tuple[dict[str, dict[int, int]], dict[int, int], int, float]:
    """Builds an inverted index: term -> {doc_id: term frequency}."""
    index: dict[str, dict[int, int]] = {}
    doc_lengths: dict[int, int] = {}

    for doc_id, doc in enumerate(corpus):
        tokens = tokenize(doc)
        if not tokens:
            continue

        doc_lengths[doc_id] = len(tokens)

        for term in tokens:
            if term not in index:
                index[term] = {}
            if doc_id not in index[term]:
                index[term][doc_id] = 1
            else:
                index[term][doc_id] += 1

    n_docs = len(doc_lengths)
    avgdl = sum(doc_lengths.values()) / n_docs if n_docs else 0.0

    return index, doc_lengths, n_docs, avgdl


def compute_idf(df: int, n_docs: int) -> float:
    """BM25 IDF (Lucene variant, +1 inside ln). Requires 0 <= df <= n_docs; result is always > 0."""
    return math.log((n_docs - df + 0.5) / (df + 0.5) + 1)


def compute_term_score(f: int, dl: int, avgdl: float, idf: float, k1: float, b: float) -> float:
    """BM25 contribution of one term to one document. Requires avgdl > 0; returns 0 for f = 0."""
    length_ratio = dl / avgdl
    k = k1 * (1 - b + b * length_ratio)
    tf = f * (k1 + 1) / (f + k)
    return idf * tf


def compute_score(doc_id: int, index: dict[str, dict[int, int]],
                  doc_lengths: dict[int, int], idfs: dict[str, float], avgdl: float,
                  k1: float = 1.5, b: float = 0.75) -> float:
    """BM25 score of one document. The keys of idfs are the deduplicated query terms;
    avgdl > 0 is guaranteed by the caller (top_m) for every known document."""
    if doc_id not in doc_lengths:       # skipped (empty) or unknown document
        return 0.0

    dl = doc_lengths[doc_id]
    score = 0.0

    for term, idf in idfs.items():
        f = index.get(term, {}).get(doc_id, 0)
        score += compute_term_score(f, dl, avgdl, idf, k1, b)

    return score


def top_m(query: str, index: dict[str, dict[int, int]], doc_lengths: dict[int, int],
          n_docs: int, avgdl: float, m: int, k1: float = 1.5, b: float = 0.75) -> list[tuple[int, float]]:
    """Returns up to m (doc_id, score) pairs with score > 0, best first; ties keep the smaller doc_id first."""
    if n_docs == 0 or m <= 0:
        return []

    terms = set(tokenize(query))
    idfs = {term: compute_idf(len(index.get(term, {})), n_docs) for term in terms}

    candidates = set()
    for term in terms:
        candidates.update(index.get(term, {}))

    scored = [(-compute_score(doc_id, index, doc_lengths, idfs, avgdl, k1, b), doc_id) for doc_id in candidates]
    best = heapq.nsmallest(m, scored)
    return [(doc_id, -negative_score) for negative_score, doc_id in best]
