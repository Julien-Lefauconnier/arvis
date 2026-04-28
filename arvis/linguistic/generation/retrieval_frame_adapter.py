# arvis/linguistic/generation/retrieval_frame_adapter.py

from arvis.cognition.retrieval.cognitive_retrieval_snapshot import (
    CognitiveRetrievalSnapshot,
)
from arvis.linguistic.generation.generation_frame import (
    LinguisticGenerationFrame,
)


def adapt_frame_with_retrieval(
    *,
    base_frame: LinguisticGenerationFrame,
    retrieval_snapshot: CognitiveRetrievalSnapshot | None,
) -> LinguisticGenerationFrame:
    """
    Adapt a linguistic generation frame using cognitive retrieval signals.

    ZKCS rules:
    - no content injection
    - no text exposure
    - no inference
    """

    if not retrieval_snapshot:
        return base_frame

    # Retrieval exists → reduce verbosity & forbid speculation
    return LinguisticGenerationFrame(
        act=base_frame.act,
        allowed_entries=base_frame.allowed_entries,
        tone=base_frame.tone,
        verbosity="minimal",
        allow_speculation=False,
    )
