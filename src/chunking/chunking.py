from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    """A piece of a document, identified by the document id and its position."""
    document_id: str
    position: int
    text: str


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


def create_chunks(document_id: str, text: str, chunk_size: int, overlap: int) -> list[Chunk]:
    """Splits the document text into Chunk objects numbered from 0."""
    if not document_id.strip():
        raise ValueError("document_id must not be empty")

    texts = split_into_chunks(text, chunk_size, overlap)
    return [Chunk(document_id, position, chunk_text) for position, chunk_text in enumerate(texts)]
