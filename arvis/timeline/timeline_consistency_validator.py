# arvis/timeline/timeline_consistency_validator.py

from dataclasses import dataclass
from typing import Iterable, Tuple, Dict, Any


@dataclass(frozen=True)
class TimelineConsistencyIssue:
    code: str
    message: str
    context: Dict[str, Any]


@dataclass(frozen=True)
class TimelineConsistencyReport:
    is_consistent: bool
    issues: Tuple[TimelineConsistencyIssue, ...]


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
