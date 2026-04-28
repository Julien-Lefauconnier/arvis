# arvis/ir/replay/replay_validator.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from arvis.ir.serialization.cognitive_ir_hasher import CognitiveIRHasher


@dataclass(frozen=True)
class ReplayResult:
    """
    Result of replay validation.
    """

    is_deterministic: bool
    original_hash: str
    replay_hash: str
    reason: str | None = None


class ReplayValidator:
    """
    Validates determinism of the CognitivePipeline.

    Guarantees:
    - reproducibility check
    - hash equality validation
    """

    @staticmethod
    def validate(
        pipeline: Any,
        input_data: dict[str, Any],
        original_ir: Any,
    ) -> ReplayResult:
        """
        Replay pipeline and compare IR hashes.
        """

        try:
            # --- original hash ---
            original_hash = CognitiveIRHasher.hash(original_ir)

            # --- replay ---
            replay_result = pipeline.run_from_input(input_data)
            replay_ir = getattr(replay_result, "ir", None)

            if replay_ir is None:
                return ReplayResult(
                    is_deterministic=False,
                    original_hash=original_hash,
                    replay_hash="",
                    reason="missing_replay_ir",
                )

            replay_hash = CognitiveIRHasher.hash(replay_ir)

            if original_hash != replay_hash:
                return ReplayResult(
                    is_deterministic=False,
                    original_hash=original_hash,
                    replay_hash=replay_hash,
                    reason="hash_mismatch",
                )

            return ReplayResult(
                is_deterministic=True,
                original_hash=original_hash,
                replay_hash=replay_hash,
                reason=None,
            )

        except Exception as e:
            return ReplayResult(
                is_deterministic=False,
                original_hash="",
                replay_hash="",
                reason=f"replay_error:{str(e)}",
            )
