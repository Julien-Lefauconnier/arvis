# tests/timeline/test_timeline_consistency_validator.py

import pytest

from arvis.timeline.timeline_consistency_validator import (
    TimelineConsistencyIssue,
    TimelineConsistencyReport,
    TimelineConsistencyValidator,
)


def test_validator_no_issues():
    report = TimelineConsistencyValidator.validate([])

    assert isinstance(report, TimelineConsistencyReport)
    assert report.is_consistent is True
    assert report.issues == ()


def test_validator_with_one_issue():
    issue = TimelineConsistencyIssue(
        code="HASHCHAIN_BROKEN",
        message="Hashchain integrity failure",
        context={"entry": "abc"},
    )

    report = TimelineConsistencyValidator.validate([issue])

    assert report.is_consistent is False
    assert len(report.issues) == 1
    assert report.issues[0] == issue


def test_validator_multiple_issues():
    issues = [
        TimelineConsistencyIssue(
            code="HASHCHAIN_BROKEN",
            message="Hash mismatch",
            context={"entry": "1"},
        ),
        TimelineConsistencyIssue(
            code="DELTA_INVALID",
            message="Delta replay failed",
            context={"entry": "2"},
        ),
    ]

    report = TimelineConsistencyValidator.validate(issues)

    assert report.is_consistent is False
    assert len(report.issues) == 2


def test_report_immutability():
    report = TimelineConsistencyReport(
        is_consistent=True,
        issues=(),
    )

    with pytest.raises(Exception):
        report.is_consistent = False


def test_issue_structure():
    issue = TimelineConsistencyIssue(
        code="TEST",
        message="Test issue",
        context={"key": "value"},
    )

    assert issue.code == "TEST"
    assert issue.message == "Test issue"
    assert issue.context["key"] == "value"
