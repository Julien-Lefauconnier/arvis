# tests/math/test_policy_tables.py
"""The decision constants live in one place and are committed to.

Campaign HARDEN (DM-H9, audit P1-9, 2026-09-02). The kappa band
thresholds existed as two verbatim copies (control stage, gate
adaptive layer) with nothing keeping them equal; the canonical
switching parameters existed twice, one copy dead, while the
bootstrap small-gain check declared its own alpha=0.3 against their
0.15; the strict theoretical-enforcement branch read a knob nothing
could write; and none of it was part of the policies fingerprint.
"""

from __future__ import annotations

import inspect

import pytest

from arvis.math.adaptive.kappa_bands import (
    KAPPA_BAND_EPSILON_FACTORS,
    kappa_band,
)
from arvis.math.switching.switching_params import DEFAULT_SWITCHING_PARAMS


@pytest.mark.parametrize(
    ("margin", "band"),
    [
        (0.5, "hard"),
        (1e-9, "hard"),
        (0.0, "critical"),
        (-0.019, "critical"),
        (-0.02, "warning"),
        (-0.049, "warning"),
        (-0.05, "stable"),
        (-1.0, "stable"),
    ],
)
def test_the_band_table_is_the_historical_mapping(margin, band) -> None:
    """Exactly the mapping both duplicated copies implemented."""
    assert kappa_band(margin) == band


def test_every_band_has_an_epsilon_factor() -> None:
    assert set(KAPPA_BAND_EPSILON_FACTORS) == {
        "hard",
        "critical",
        "warning",
        "stable",
    }
    assert KAPPA_BAND_EPSILON_FACTORS["stable"] == 1.0


def test_the_consumers_read_the_table_not_literals() -> None:
    """No copy of the thresholds survives in the two consumers."""
    from arvis.kernel.pipeline.stages import control_stage
    from arvis.kernel.pipeline.stages.gate import adaptive

    for module in (control_stage, adaptive):
        src = inspect.getsource(module)
        assert "-0.02" not in src, f"{module.__name__} keeps a threshold copy"
        assert "-0.05" not in src, f"{module.__name__} keeps a threshold copy"
        assert "kappa_band" in src


def test_the_bootstrap_small_gain_uses_the_canonical_parameters() -> None:
    """DM-H9c: the check used to declare alpha=0.3 against the
    parameter set's 0.15 (the 'defaults passing by construction'
    class); it must consume the single source."""
    from arvis.kernel.pipeline.services import pipeline_bootstrap_service

    src = inspect.getsource(pipeline_bootstrap_service)
    assert "DEFAULT_SWITCHING_PARAMS.alpha" in src
    assert "alpha=0.3" not in src


def test_the_dead_switching_copy_stays_deleted() -> None:
    from arvis.kernel.pipeline import cognitive_pipeline

    assert not hasattr(cognitive_pipeline, "DEFAULT_SWITCHING_PARAMS")


def test_the_preparation_service_uses_the_canonical_parameters() -> None:
    from arvis.kernel.pipeline.services.pipeline_preparation_service import (
        PipelinePreparationService,
    )

    assert (
        PipelinePreparationService.DEFAULT_SWITCHING_PARAMS is DEFAULT_SWITCHING_PARAMS
    )


def test_the_policies_fingerprint_commits_to_the_tables(monkeypatch) -> None:
    """A build that changes a band threshold or a switching parameter
    is a differently governed build: the fingerprint must move."""
    from arvis.api import commitment

    baseline = commitment.policies_fingerprint()
    monkeypatch.setattr(
        commitment, "KAPPA_BAND_CRITICAL_THRESHOLD", -0.03, raising=True
    )
    assert commitment.policies_fingerprint() != baseline


def test_strict_enforcement_is_a_reachable_declared_posture() -> None:
    """DM-H9d: the knob is a declared context field with a typed
    default; a host setting STRICT reaches the strict branch."""
    from arvis.kernel.pipeline.cognitive_pipeline_context import (
        CognitivePipelineContext,
    )
    from arvis.math.gate.gate_postures import TheoreticalEnforcementMode

    ctx = CognitivePipelineContext(user_id="u", cognitive_input="x")
    assert ctx.theoretical_enforcement_mode is TheoreticalEnforcementMode.MONITOR
    ctx.theoretical_enforcement_mode = TheoreticalEnforcementMode.STRICT
    assert ctx.theoretical_enforcement_mode == "strict"
