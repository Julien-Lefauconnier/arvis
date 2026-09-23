"""RED contract for ARVIS CTX1 host context availability.

CTX1 adds one trusted, content-free host signal saying that relevant context
for the current turn has already been assembled and authorized by the host.

The host keeps ownership of transcript loading, retrieval, source selection,
workspace isolation and relevance. ARVIS receives no transcript here.
"""

from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest

import arvis.host_api
from arvis import ArvisEngine, CognitiveOS
from arvis.cognition.decision.decision_evaluator import DecisionEvaluator


def _frames(signal: object) -> tuple[str, ...]:
    values = getattr(signal, "uncertainty_frames", ())
    return tuple(str(getattr(frame, "frame_id", "")) for frame in values)


def _contextual_input() -> dict[str, object]:
    return {
        "input_id": "ctx1",
        "intent_type": "question",
        "context_dependent": 1.0,
    }


def test_host_api_version_advances_for_ctx1_additive_engine_contract() -> None:
    major, minor = arvis.host_api.HOST_API_VERSION.split(".", maxsplit=1)
    assert (int(major), int(minor)) >= (1, 4)


def test_run_shaped_public_methods_expose_keyword_only_host_context_available() -> None:
    targets = (
        CognitiveOS.run,
        CognitiveOS.run_as,
        CognitiveOS.run_ir,
        ArvisEngine.run,
        ArvisEngine.run_as,
        ArvisEngine.ask,
        ArvisEngine.run_ir,
    )

    for target in targets:
        parameter = inspect.signature(target).parameters.get("host_context_available")
        assert parameter is not None, target
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY, target
        assert parameter.default is False, target
        assert parameter.annotation in (bool, "bool"), target


def test_typed_host_context_availability_resolves_context_gap_without_memory() -> None:
    ctx = SimpleNamespace(
        cognitive_input=_contextual_input(),
        memory_projection=None,
        extra={},
        host_context_available=True,
    )

    signal = DecisionEvaluator().evaluate(ctx)

    assert "CONTEXTUAL" not in _frames(signal)
    assert signal.memory_influence["memory_present"] is False


def test_request_payload_or_extra_cannot_spoof_trusted_context_availability() -> None:
    cognitive_input = _contextual_input()
    cognitive_input["host_context_available"] = True

    ctx = SimpleNamespace(
        cognitive_input=cognitive_input,
        memory_projection=None,
        extra={"host_context_available": True},
    )

    signal = DecisionEvaluator().evaluate(ctx)

    assert "CONTEXTUAL" in _frames(signal)


def test_public_channel_is_committed_and_replayed_without_raw_context() -> None:
    os = CognitiveOS()

    view = os.run(
        user_id="ctx1-user",
        cognitive_input=_contextual_input(),
        host_context_available=True,
    )
    ir = view.to_ir()

    assert ir is not None
    context = ir["context"]
    assert isinstance(context, dict)
    context_extra = context["extra"]
    assert isinstance(context_extra, dict)
    assert context_extra["host_context_available"] is True

    input_ir = ir["input"]
    assert isinstance(input_ir, dict)
    metadata = input_ir["metadata"]
    assert isinstance(metadata, dict)
    assert "host_context_available" not in metadata

    assert view.global_commitment is not None
    replayed = os.replay_verified(
        ir,
        expected_global_commitment=view.global_commitment,
    )
    assert replayed.to_ir() == ir


def test_default_false_omits_the_host_context_marker() -> None:
    ir = CognitiveOS().run_ir(
        user_id="ctx1-default",
        cognitive_input={"input_id": "ctx1-default"},
        host_context_available=False,
    )

    context = ir["context"]
    assert isinstance(context, dict)
    context_extra = context["extra"]
    assert isinstance(context_extra, dict)
    assert "host_context_available" not in context_extra


def test_non_bool_host_context_is_rejected_after_parameter_exists() -> None:
    parameter = inspect.signature(CognitiveOS.run).parameters.get(
        "host_context_available"
    )
    assert parameter is not None

    with pytest.raises(TypeError, match="host_context_available"):
        CognitiveOS().run(
            user_id="ctx1-invalid",
            cognitive_input={"input_id": "ctx1-invalid"},
            host_context_available=1,  # type: ignore[arg-type]
        )
