"""sources package; re-exports the module so that `import sources` works from src and from inside the folder."""
from .sources import (
    ARXIV_API_URL,
    ArxivSource,
    Document,
    PEER_REVIEW_OVERFETCH,
    SearchFilter,
    Source,
    SourceError,
    build_arxiv_url,
    ORIGINS,
    http_get,
    http_get_bytes,
    normalize_keywords,
    parse_arxiv_feed,
)
