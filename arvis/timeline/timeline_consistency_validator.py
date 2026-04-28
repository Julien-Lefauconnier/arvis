# arvis/timeline/timeline_consistency_validator.py

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TimelineConsistencyIssue:
    code: str
    message: str
    context: dict[str, Any]


@dataclass(frozen=True)
class TimelineConsistencyReport:
    is_consistent: bool
    issues: tuple[TimelineConsistencyIssue, ...]


class TimelineConsistencyValidator:
    """
    Kernel-level timeline consistency validator.
    """

    @staticmethod
    def validate(
        issues: Iterable[TimelineConsistencyIssue],
    ) -> TimelineConsistencyReport:
        issues = tuple(issues)

        return TimelineConsistencyReport(
            is_consistent=len(issues) == 0,
            issues=issues,
        )
