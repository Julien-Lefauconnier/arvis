# arvis/reflexive/compliance/reflexive_explanation.py

from __future__ import annotations

from typing import Any


class ReflexiveExplanation:
    """
    Structured, deterministic explanation object for reflexive exposure.

    ⚠️ Important:
    - No natural language generation
    - Pure data structure
    - Fully deterministic & testable
    """

    def __init__(
        self,
        *,
        has_timeline: bool = True,
        public: bool = False,
        limitations: list[str] | None = None,
    ):
        self.has_timeline = has_timeline
        self.public = public
        self.limitations: list[str] = limitations or []

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def default(cls) -> ReflexiveExplanation:
        return cls()

    # ------------------------------------------------------------------
    # Mutators (fluent style)
    # ------------------------------------------------------------------

    def without_timeline(self) -> ReflexiveExplanation:
        return ReflexiveExplanation(
            has_timeline=False,
            public=self.public,
            limitations=list(self.limitations),
        )

    def with_public_timeline(self) -> ReflexiveExplanation:
        return ReflexiveExplanation(
            has_timeline=self.has_timeline,
            public=True,
            limitations=list(self.limitations),
        )

    def with_additional_limitations(
        self,
        limits: list[str],
    ) -> ReflexiveExplanation:
        return ReflexiveExplanation(
            has_timeline=self.has_timeline,
            public=self.public,
            limitations=[*self.limitations, *limits],
        )

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "has_timeline": self.has_timeline,
            "public": self.public,
            "limitations": list(self.limitations),
        }

    # ------------------------------------------------------------------
    # Debug / repr (optional but useful for tests)
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"ReflexiveExplanation("
            f"has_timeline={self.has_timeline}, "
            f"public={self.public}, "
            f"limitations={self.limitations})"
        )
