# tests/kernel/pipeline/services/test_strict_mode_channel.py

"""Strict mode channel contract (F-009).

CognitiveOSConfig.strict_mode must have a real effect on the stability
bootstrap: it is forwarded to PipelineBootstrapService and combined
monotonically with the ARVIS_STRICT_STABILITY env var. Either channel
can enable the strict profile; neither can disable the other.
"""

import pytest

from arvis.api.engine import ArvisEngine
from arvis.api.os import CognitiveOS, CognitiveOSConfig
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.services import pipeline_bootstrap_service as pbs


@pytest.fixture
def failing_small_gain(monkeypatch):
    """Force the bootstrap small-gain invariant check to fail."""
    monkeypatch.setattr(
        pbs.CompositeLyapunov,
        "check_small_gain",
        lambda self, eta=0.05, alpha=0.3, L_T=1.0: False,
    )
    monkeypatch.delenv("ARVIS_STRICT_STABILITY", raising=False)


def test_default_mode_warns_instead_of_raising(failing_small_gain):
    with pytest.warns(RuntimeWarning, match="small-gain"):
        CognitivePipeline()


def test_pipeline_strict_mode_raises(failing_small_gain):
    with pytest.raises(RuntimeError, match="small-gain"):
        CognitivePipeline(strict_mode=True)


def test_config_strict_mode_reaches_bootstrap(failing_small_gain):
    with pytest.raises(RuntimeError, match="small-gain"):
        CognitiveOS(CognitiveOSConfig(strict_mode=True))


def test_engine_kwargs_strict_mode_reaches_bootstrap(failing_small_gain):
    with pytest.raises(RuntimeError, match="small-gain"):
        ArvisEngine(strict_mode=True)


def test_env_channel_still_enables_strict(failing_small_gain, monkeypatch):
    monkeypatch.setenv("ARVIS_STRICT_STABILITY", "true")
    with pytest.raises(RuntimeError, match="small-gain"):
        CognitivePipeline()


def test_config_false_does_not_disable_env(failing_small_gain, monkeypatch):
    monkeypatch.setenv("ARVIS_STRICT_STABILITY", "true")
    with pytest.raises(RuntimeError, match="small-gain"):
        CognitiveOS(CognitiveOSConfig(strict_mode=False))
