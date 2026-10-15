def split_into_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Splits the text into chunks of chunk_size words; neighbouring chunks share overlap words."""
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be > 0 and 0 <= overlap < chunk_size")

    words = text.split()
    step = chunk_size - overlap
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start += step

    return chunks
