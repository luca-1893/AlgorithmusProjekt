import math


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
