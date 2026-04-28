# arvis/reflexive/timeline/explanation/reflexive_timeline_exposure_explanation.py

from collections.abc import Iterable
from typing import Any, cast

from arvis.reflexive.compliance.reflexive_explanation import (
    ReflexiveExplanation,
)


class ReflexiveTimelineExposureExplanation:
    """
    Declarative explanation of timeline exposure.
    """

    PUBLIC_FACTUAL_ROLES = {"public", "exposed", "user_visible", "trace_factuelle"}

    @classmethod
    def build(
        cls,
        roles: Iterable[Any],
        *,
        has_any_public_view: bool = False,
    ) -> dict[str, Any]:
        normalized_roles: list[str] = []

        for role in roles:
            if role is None:
                continue
            value = getattr(role, "value", role)
            normalized_roles.append(str(value))

        unique_roles = sorted(set(normalized_roles))

        explanation = cast(Any, ReflexiveExplanation.default())

        if not unique_roles and not has_any_public_view:
            return cast(dict[str, Any], explanation.without_timeline().to_dict())

        if not unique_roles and has_any_public_view:
            return cast(
                dict[str, Any],
                explanation.with_additional_limitations(
                    ["Non-factual public views are exposed"]
                ).to_dict(),
            )

        if any(r in cls.PUBLIC_FACTUAL_ROLES for r in unique_roles):
            explanation = explanation.with_public_timeline()

        other_roles = [r for r in unique_roles if r not in cls.PUBLIC_FACTUAL_ROLES]
        if other_roles:
            explanation = explanation.with_additional_limitations(
                ["Some exposed views are not factual"]
            )

        return cast(dict[str, Any], explanation.to_dict())
