"""pipeline package; re-exports the module so that `import pipeline` works from src and from inside the folder."""
from .pipeline import (
    Hit,
    PipelineConfig,
    ResearchResult,
    research,
)
