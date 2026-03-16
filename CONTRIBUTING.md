# Contributing to ARVIS-POSIX

ARVIS-POSIX is a formal specification — not a framework.  
Contributions should focus on improving clarity, correctness, or coverage of the invariants and interfaces.

## How to Contribute

1. Read `docs/ARCHITECTURE_INVARIANTS.md` first — all proposals must respect them.
2. Propose changes to:
   - Invariants (docs/*.md)
   - Abstract interfaces (interfaces/*.py)
   - Compliance tests (compliance/*.py)
   - Examples (examples/*.py)
3. Open an issue first for discussion (especially for new primitives or major changes).
4. Submit a PR with:
   - Clear description
   - References to affected invariants
   - Tests if applicable

## Scope for v0.1

Focus on:
- Mathematical stability invariants
- Cognitive Bundle & Timeline primitives
- Reflexive Snapshot & Self-Model
- Declarative contracts

Conversation orchestration is partially covered (stability invariants only).

Thank you for helping build a disciplined cognitive standard.