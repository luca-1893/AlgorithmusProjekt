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

