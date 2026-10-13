JOINERS = "-–—'’"


def tokenize(chunk: str) -> list[str]:
    """Normalizes the chunk into a list of casefolded words, stripped of punctuation."""
    folded = chunk.casefold()
    joined = "".join(char for char in folded if char not in JOINERS)
    cleaned = "".join(char if char.isalnum() else " " for char in joined)
    tokens = cleaned.split()
    return tokens
