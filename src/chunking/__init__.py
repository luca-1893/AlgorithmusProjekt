"""chunking package; re-exports the module so that `import chunking` works from src and from inside the folder."""
from .chunking import (
    Chunk,
    create_chunks,
    split_into_chunks,
)
