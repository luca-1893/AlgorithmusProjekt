"""vector_search package; re-exports the module so that `import vector_search` works from src and from inside the folder."""
from .vector_search import (
    Embedder,
    EmbeddingError,
    cosine_similarity,
    mmr_select,
    most_similar,
    top_k,
)
