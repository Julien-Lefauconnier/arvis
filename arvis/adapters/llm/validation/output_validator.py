# arvis/adapters/llm/validation/output_validator.py

import json
from dataclasses import dataclass
from enum import StrEnum
from json import JSONDecodeError
from typing import Any

from pydantic import BaseModel, ValidationError


@dataclass(frozen=True)
class LLMValidationError:
    code: str
    message: str


@dataclass(frozen=True)
class LLMValidationSeverity(StrEnum):
    OK = "ok"
    RETRYABLE = "retryable"
    FATAL = "fatal"
    ABSTENTION_REQUIRED = "abstention_required"


@dataclass(frozen=True)
class LLMValidationResult:
    is_valid: bool
    severity: LLMValidationSeverity
    errors: list[LLMValidationError]
    parsed: Any | None = None


class LLMOutputValidator:
    """
    Validates LLM outputs against ARVIS governance constraints.
    """

    @staticmethod
    def validate(
        content: str | None,
        *,
        require_abstention: bool = False,
    ) -> LLMValidationResult:
        # --- 1. Empty / null response ---
        if content is None or not content.strip():
            return LLMValidationResult(
                is_valid=False,
                severity=LLMValidationSeverity.FATAL,
                errors=[
                    LLMValidationError(
                        code="empty_output",
                        message="LLM output is empty or null.",
                    )
                ],
            )

        normalized = content.lower()

        # --- 2. Abstention enforcement ---
        if require_abstention:
            if not LLMOutputValidator._contains_abstention(normalized):
                return LLMValidationResult(
                    is_valid=False,
                    severity=LLMValidationSeverity.ABSTENTION_REQUIRED,
                    errors=[
                        LLMValidationError(
                            code="missing_abstention",
                            message="Expected abstention but none detected.",
                        )
                    ],
                )

        # --- 3. Chain-of-thought leakage ---
        if LLMOutputValidator._detect_cot_leak(normalized):
            return LLMValidationResult(
                is_valid=False,
                severity=LLMValidationSeverity.RETRYABLE,
                errors=[
                    LLMValidationError(
                        code="cot_leak_detected",
                        message="Chain-of-thought leakage detected.",
                    )
                ],
            )

        return LLMValidationResult(
            is_valid=True,
            severity=LLMValidationSeverity.OK,
            errors=[],
        )

    # -----------------------------
    # Internal helpers
    # -----------------------------
    @staticmethod
    def validate_structured(
        content: str | None,
        *,
        schema: type[Any],
        require_abstention: bool = False,
    ) -> LLMValidationResult:
        base = LLMOutputValidator.validate(
            content,
            require_abstention=require_abstention,
        )

        if not base.is_valid:
            return base

        if content is None:
            return LLMValidationResult(
                is_valid=False,
                severity=LLMValidationSeverity.FATAL,
                errors=[
                    LLMValidationError(
                        code="empty_output",
                        message="LLM output is empty or null.",
                    )
                ],
            )

        try:
            data = json.loads(content)

        except JSONDecodeError as exc:
            return LLMValidationResult(
                is_valid=False,
                severity=LLMValidationSeverity.RETRYABLE,
                errors=[
                    LLMValidationError(
                        code="invalid_json",
                        message=f"Output is not valid JSON: {exc.msg}",
                    )
                ],
            )

        try:
            if issubclass(schema, BaseModel):
                parsed = schema.model_validate(data)
            else:
                parsed = schema(**data)

        except ValidationError as exc:
            return LLMValidationResult(
                is_valid=False,
                severity=LLMValidationSeverity.RETRYABLE,
                errors=[
                    LLMValidationError(
                        code="schema_validation_failed",
                        message=str(exc),
                    )
                ],
            )

        except TypeError as exc:
            return LLMValidationResult(
                is_valid=False,
                severity=LLMValidationSeverity.RETRYABLE,
                errors=[
                    LLMValidationError(
                        code="schema_instantiation_failed",
                        message=str(exc),
                    )
                ],
            )

        return LLMValidationResult(
            is_valid=True,
            severity=LLMValidationSeverity.OK,
            errors=[],
            parsed=parsed,
        )

    @staticmethod
    def _contains_abstention(text: str) -> bool:
        patterns = [
            "i cannot answer",
            "i don't have enough information",
            "insufficient information",
            "i cannot determine",
            "i am unable to",
            "not enough context",
        ]
        return any(p in text for p in patterns)

    @staticmethod
    def _detect_cot_leak(text: str) -> bool:
        cot_patterns = [
            "let's think step by step",
            "step 1",
            "step-by-step",
            "reasoning:",
            "chain of thought",
        ]
        return any(p in text for p in cot_patterns)
