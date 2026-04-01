# arvis/ir/validation/cognitive_ir_validator.py

from __future__ import annotations

from arvis.ir.cognitive_ir import CognitiveIR
from arvis.ir.gate import CognitiveGateVerdictIR, CognitiveGateIR


class CognitiveIRValidationError(Exception):
    pass


class CognitiveIRValidator:
    """
    PRODUCTION validator (STRICT)

    - deterministic
    - no silent fallback
    - raises on violation
    """

    @classmethod
    def validate(cls, ir: CognitiveIR) -> None:
        if ir is None:
            raise CognitiveIRValidationError("IR is None")

        cls._validate_presence(ir)

        # 🔒 extract once (mypy-safe)
        gate = ir.gate
        assert gate is not None  # guaranteed by presence

        cls._validate_gate(gate)
        cls._validate_reason_codes(gate)
        cls._validate_trace(gate)
        cls._validate_consistency(ir, gate)

    # -----------------------------------------
    # PRESENCE
    # -----------------------------------------
    @staticmethod
    def _validate_presence(ir: CognitiveIR) -> None:
        if ir.input is None:
            raise CognitiveIRValidationError("Missing input IR")

        if ir.context is None:
            raise CognitiveIRValidationError("Missing context IR")

        if ir.gate is None:
            raise CognitiveIRValidationError("Missing gate IR")

    # -----------------------------------------
    # GATE
    # -----------------------------------------
    @staticmethod
    def _validate_gate(gate: CognitiveGateIR) -> None:
        verdict = gate.verdict

        if verdict not in (
            CognitiveGateVerdictIR.ALLOW,
            CognitiveGateVerdictIR.REQUIRE_CONFIRMATION,
            CognitiveGateVerdictIR.ABSTAIN,
        ):
            raise CognitiveIRValidationError(f"Invalid verdict: {verdict}")

    # -----------------------------------------
    # REASON CODES
    # -----------------------------------------
    @staticmethod
    def _validate_reason_codes(gate: CognitiveGateIR) -> None:
        codes = gate.reason_codes

        if not isinstance(codes, tuple):
            raise CognitiveIRValidationError("reason_codes must be tuple")

        if len(codes) == 0:
            raise CognitiveIRValidationError("reason_codes empty")

        for c in codes:
            if not isinstance(c, str) or not c.strip():
                raise CognitiveIRValidationError(f"Invalid reason_code: {c}")

    # -----------------------------------------
    # TRACE
    # -----------------------------------------
    @staticmethod
    def _validate_trace(gate: CognitiveGateIR) -> None:
        trace = gate.decision_trace

        if trace is None:
            return

        for step in trace:
            if not step.stage:
                raise CognitiveIRValidationError("Trace step missing stage")

            if step.severity < 0:
                raise CognitiveIRValidationError("Negative severity")

            if not isinstance(step.reason_codes, tuple):
                raise CognitiveIRValidationError("Invalid step reason_codes")

    # -----------------------------------------
    # CONSISTENCY RULES
    # -----------------------------------------
    @staticmethod
    def _validate_consistency(ir: CognitiveIR, gate: CognitiveGateIR) -> None:
        verdict = gate.verdict
        codes = set(gate.reason_codes)

        # -----------------------------------------
        # Detect override context
        # -----------------------------------------
        is_override = False

        context = ir.context
        if context is not None:
            extra = getattr(context, "extra", None)
            if isinstance(extra, dict):
                is_override = bool(extra.get("confirmation_override", False))

        # -----------------------------------------
        # ALLOW consistency
        # -----------------------------------------
        if verdict == CognitiveGateVerdictIR.ALLOW:
            forbidden = {
                "adaptive_instability_veto",
                "kappa_violation",
                "projection_invalid",
            }

            violations = codes & forbidden

            if violations:
                if is_override:
                    return

                raise CognitiveIRValidationError(
                    f"Inconsistent ALLOW with veto signals: {violations}"
                )

        # -----------------------------------------
        # ABSTAIN
        # -----------------------------------------
        if verdict == CognitiveGateVerdictIR.ABSTAIN:
            if not codes:
                raise CognitiveIRValidationError("ABSTAIN without reason")

        # -----------------------------------------
        # REQUIRE_CONFIRMATION
        # -----------------------------------------
        if verdict == CognitiveGateVerdictIR.REQUIRE_CONFIRMATION:
            if len(codes) == 0:
                raise CognitiveIRValidationError("Confirmation without reason")