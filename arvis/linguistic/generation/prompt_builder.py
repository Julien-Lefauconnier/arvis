# arvis/linguistic/generation/prompt_builder.py

from arvis.linguistic.generation.generation_frame import (
    LinguisticGenerationFrame,
)


def build_llm_prompt(
    *,
    frame: LinguisticGenerationFrame,
    context: str,
    query: str,
) -> str:
    """
    Build a constrained LLM prompt from a linguistic generation frame.

    This function is PURE:
    - no side effects
    - no LLM dependency
    - fully testable
    """

    rules = [
        f"- Act: {frame.act.value}",
        "- Do NOT speculate",
        "- Do NOT invent facts",
        "- Do NOT introduce new actions",
        "- Use only the allowed vocabulary when possible",
    ]

    if frame.allowed_entries:
        rules.append("- Allowed key terms: " + ", ".join(frame.allowed_entries))

    if frame.tone:
        rules.append(f"- Tone: {frame.tone}")

    if frame.verbosity:
        rules.append(f"- Verbosity: {frame.verbosity}")

    if frame.constraints:
        rules.append("- Respect constraints: " + ", ".join(frame.constraints))

    system_block = "\n".join(rules)

    return (
        "SYSTEM CONSTRAINTS:\n"
        f"{system_block}\n\n"
        "CONTEXT:\n"
        f"{context or '[no external context]'}\n\n"
        "USER QUERY:\n"
        f"{query}\n\n"
        "RESPONSE:"
    )
