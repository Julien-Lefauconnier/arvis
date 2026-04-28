# arvis/knowledge/knowledge_signal.py

from enum import StrEnum


class KnowledgeSignal(StrEnum):
    """
    Declarative signals explaining *why* a given KnowledgeState was reached.

    A KnowledgeSignal is:
    - observable
    - non-sensitive
    - non-semantic
    - non-decisional

    It does NOT:
    - assert truth
    - store content
    - trigger behavior
    - enforce policy
    """

    # Not enough internal or external signals to support an answer
    INSUFFICIENT_INFORMATION = "insufficient_information"

    # Conflicting signals detected across sources or reasoning paths
    CONFLICTING_SIGNALS = "conflicting_signals"

    # The answer depends strongly on context not fully specified
    CONTEXT_DEPENDENT = "context_dependent"

    # High variance detected between plausible interpretations
    HIGH_VARIANCE = "high_variance"

    # Knowledge exists but is outdated or unstable
    UNSTABLE_KNOWLEDGE = "unstable_knowledge"

    # The system explicitly detects a known limitation
    SYSTEM_LIMITATION = "system_limitation"

    # The question falls outside supported domains
    OUT_OF_SCOPE = "out_of_scope"

    # Knowledge is inferred indirectly, not directly supported
    INDIRECT_KNOWLEDGE = "indirect_knowledge"
