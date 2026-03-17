# arvis/knowledge/knowledge_state.py

from enum import Enum


class KnowledgeState(str, Enum):
    """
    Declarative representation of Veramem's knowledge awareness.

    This is NOT:
    - confidence
    - correctness
    - response quality

    It is a structural signal used to model
    what the system knows or does not know.
    """

    # The system has no reliable knowledge on the subject
    UNKNOWN = "unknown"

    # The system has partial, fragmented or indirect knowledge
    PARTIAL = "partial"

    # The system has stable, well-supported knowledge
    KNOWN = "known"

    # The system detects ambiguity, contradiction or instability
    UNCERTAIN = "uncertain"

    # The system explicitly knows it cannot answer reliably
    NOT_APPLICABLE = "not_applicable"
