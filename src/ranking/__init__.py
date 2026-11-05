"""ranking package; re-exports the module so that `import ranking` works from src and from inside the folder."""
from .ranking import (
    normalize_scores,
    reciprocal_rank_fusion,
)
