# arvis/linguistic/invariants.py

"""
Linguistic invariants — ZKCS / ARVIS

This module defines the non-negotiable invariants governing the linguistic layer.

These invariants exist to prevent architectural drift and ensure that the
linguistic layer never becomes:
- a reasoning system
- an adaptive learning system
- a probabilistic feedback loop
- a hidden decision-making mechanism

The linguistic layer is declarative, explicit, optional, and fully governed
by human authority.

Any future implementation MUST comply with the invariants defined here.
"""


class LinguisticInvariants:
    """
    Normative invariants for the linguistic layer.

    These rules are conceptual constraints. They are not configuration options
    and must never be bypassed.
    """

    #: The linguistic layer MUST NOT influence cognition or decision-making.
    NO_COGNITIVE_INFLUENCE = True

    #: The linguistic layer MUST NOT perform inference, generalization, or learning.
    NO_INFERENCE = True

    #: The linguistic layer MUST NOT auto-modify itself.
    NO_SELF_MODIFICATION = True

    #: Any linguistic change MUST be explicitly proposed and validated by a human.
    HUMAN_VALIDATION_REQUIRED = True

    #: Linguistic changes MUST be declarative, versioned, and reversible.
    DECLARATIVE_AND_VERSIONED = True

    #: The LLM MUST remain interchangeable and unconstrained at the cognition level.
    LLM_PROVIDER_INDEPENDENCE = True
