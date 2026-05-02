# arvis/adapters/llm/prompts/templates.py

from __future__ import annotations

INTENT_ENRICHMENT_SYSTEM_PROMPT = (
    "You are a cognitive assistant operating inside ARVIS, "
    "a governed Cognitive OS. Follow the provided constraints strictly."
)

INTENT_ENRICHMENT_USER_TEMPLATE = """
Intent:
{intent}

Provide:
- a short execution plan
- potential risks
- optional refinement

Keep it structured and concise.
"""
