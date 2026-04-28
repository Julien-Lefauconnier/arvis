# tests/integration/test_pipeline_replay_determinism.py

from arvis.api import CognitiveOS


def test_pipeline_replay_determinism():
    from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
    from arvis.kernel.pipeline.cognitive_pipeline_context import (
        CognitivePipelineContext,
    )

    pipeline = CognitivePipeline()

    ctx = CognitivePipelineContext(
        user_id="user-1",
        cognitive_input={"input_id": "test"},
    )

    # run normal
    result_1 = pipeline.run(ctx)

    assert result_1.cognitive_ir is not None
    assert result_1.ir_hash is not None

    # replay from IR
    result_2 = pipeline.run_from_ir(result_1.cognitive_ir)

    assert result_2.ir_hash == result_1.ir_hash


def test_os_replay_preserves_global_commitment():
    os = CognitiveOS()

    original = os.run(
        user_id="user-1",
        cognitive_input={"input_id": "test"},
    )

    ir = original.to_ir()

    assert ir is not None
    assert original.global_commitment is not None

    replayed = os.replay(
        ir,
        expected_global_commitment=original.global_commitment,
    )

    assert replayed.global_commitment == original.global_commitment


def test_os_replay_detects_global_commitment_mismatch():
    os = CognitiveOS()

    original = os.run(user_id="user-1", cognitive_input={"input_id": "test"})

    ir = original.to_ir()
    assert ir is not None

    bad_commitment = "0" * 64

    try:
        os.replay(ir, expected_global_commitment=bad_commitment)
        assert False, "expected replay verification failure"
    except RuntimeError as exc:
        assert "global_commitment mismatch" in str(exc)
