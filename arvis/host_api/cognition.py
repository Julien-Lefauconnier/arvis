# arvis/host_api/cognition.py

"""Cognitive inputs a host injects into a run.

The retrieval snapshot carrying grounded, host-side retrieval
results into the governed pipeline.

Re-export layer only: every symbol is defined where it lives; this
module pins the import path (see VERSIONING.md, host integration
surface).
"""

from arvis.cognition.retrieval.cognitive_retrieval_snapshot import (
    CognitiveRetrievalSnapshot,
)

__all__ = [
    "CognitiveRetrievalSnapshot",
]
