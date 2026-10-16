import argparse
from typing import Annotated, Optional

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from pipeline import PipelineConfig, research
from sources import ArxivSource, Source, SourceError
from vector_search import Embedder, EmbeddingError, VoyageEmbedder

MAX_K = 20
SERVER_NAME = "AlgorithmusProjekt Recherche"
INSTRUCTIONS = (
    "Searches scientific papers on arXiv and returns only the most relevant passages with their source. "
    "Use it instead of reading many papers yourself, and cite the returned title and url."
)


def default_embedder() -> Optional[Embedder]:
    """Voyage if VOYAGE_API_KEY is set, otherwise None (BM25 only)."""
    try:
        return VoyageEmbedder()
    except EmbeddingError:
        return None


def build_server(source: Optional[Source] = None, embedder: Optional[Embedder] = None,
                 config: PipelineConfig = PipelineConfig()) -> FastMCP:
    """Creates the MCP server with the research_papers tool."""
    source = source or ArxivSource()
    server = FastMCP(SERVER_NAME, instructions=INSTRUCTIONS)

    @server.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    def research_papers(
        keywords: Annotated[list[str], Field(description="2 to 8 English technical terms, e.g. ['UML', 'class diagram']")],
        k: Annotated[int, Field(description=f"Number of passages to return, 1 to {MAX_K}")] = 5,
        question: Annotated[str, Field(description="The user's original question in any language, improves ranking")] = "",
    ) -> dict:
        """Finds scientific papers for the keywords and returns the k most relevant passages with title, authors, date and url."""
        if not 1 <= k <= MAX_K:
            raise ToolError(f"k must be between 1 and {MAX_K}")
        try:
            return research(keywords, k, source, embedder, question, config).to_dict()
        except ValueError as error:
            raise ToolError(str(error)) from error
        except SourceError as error:
            raise ToolError(f"research source not reachable: {error}") from error

    return server


def main(argv: Optional[list[str]] = None) -> None:
    """Starts the server via stdio (default) or HTTP."""
    parser = argparse.ArgumentParser(description=SERVER_NAME)
    parser.add_argument("--transport", choices=("stdio", "http"), default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    server = build_server(embedder=default_embedder())
    if args.transport == "http":
        server.run(transport="http", host=args.host, port=args.port)
    else:
        server.run()
