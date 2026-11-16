def reciprocal_rank_fusion(rankings: list[list[int]], k_rrf: int = 60) -> list[tuple[int, float]]:
    """Fuses rankings of candidate ids into (id, score) pairs, best first; ties keep the lower id first."""
    if k_rrf < 0:
        raise ValueError("k_rrf must not be negative")

    scores = {}
    for ranking in rankings:
        for rank, candidate_id in enumerate(ranking, start=1):
            # only the rank counts, not the raw score: BM25 and cosine values have different scales;
            # k_rrf damps the gap between the top ranks
            scores[candidate_id] = scores.get(candidate_id, 0.0) + 1 / (k_rrf + rank)

    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))


def normalize_scores(scores: list[float]) -> list[float]:
    """Scales scores to the range 0 to 1 (min-max); all-equal scores become 1.0."""
    if not scores:
        return []
    low, high = min(scores), max(scores)
    if high == low:
        return [1.0] * len(scores)
    return [(score - low) / (high - low) for score in scores]
