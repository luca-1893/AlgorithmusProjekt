def reciprocal_rank_fusion(rankings: list[list[int]], k_rrf: int = 60) -> list[tuple[int, float]]:
    """Fuses rankings of candidate ids into (id, score) pairs, best first; ties keep the lower id first."""
    if k_rrf < 0:
        raise ValueError("k_rrf must not be negative")

    scores = {}
    for ranking in rankings:
        for rank, candidate_id in enumerate(ranking, start=1):
            scores[candidate_id] = scores.get(candidate_id, 0.0) + 1 / (k_rrf + rank)

    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))
