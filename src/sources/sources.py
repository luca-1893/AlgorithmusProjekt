from urllib.parse import urlencode

ARXIV_API_URL = "https://export.arxiv.org/api/query"


def normalize_keywords(keywords: list[str]) -> list[str]:
    """Strips and collapses whitespace, drops empty keywords and case-insensitive duplicates."""
    result = []
    seen = set()
    for keyword in keywords:
        cleaned = " ".join(keyword.split())
        key = cleaned.casefold()
        if cleaned and key not in seen:
            result.append(cleaned)
            seen.add(key)
    return result


def build_arxiv_url(keywords: list[str], max_results: int, categories: tuple[str, ...] = ()) -> str:
    """Builds the arXiv query URL; keywords are OR-combined, categories restrict the search."""
    if not keywords:
        raise ValueError("keywords must not be empty")
    if max_results <= 0:
        raise ValueError("max_results must be > 0")

    query = " OR ".join(f'all:"{keyword}"' for keyword in keywords)
    if categories:
        category_filter = " OR ".join(f"cat:{category}" for category in categories)
        query = f"({query}) AND ({category_filter})"

    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    return f"{ARXIV_API_URL}?{urlencode(params)}"
