# ARVIS

**The Cognitive Operating System for Governed AI Systems**

> Python 3.11+ • Deterministic • Replayable • Governed • Auditable

> **Status: `0.1.0-alpha` (preview).** The public API is not yet stable.
> The projection layer is partial, LLM governance is mock-first, and formal
> guarantees apply only to the documented projected domains. See
> [Known Limitations](#known-limitations-010-alpha).

ARVIS is a deterministic runtime layer that treats reasoning as **critical infrastructure**.

It provides governed cognition, replayable decisions, inspectable state transitions, controlled execution, explicit uncertainty handling, and verifiable audit trails.

> Not a model.
> Not an agent wrapper.
> Not prompt engineering.
> **ARVIS is the systems layer reliable AI should run on.**

---

## Why ARVIS Exists

Most AI systems still follow:

```text
input → model → output
```

Useful for many tasks, but weak when systems must be:

* reproducible
* auditable
* policy-constrained
* stable under pressure
* safe with tools
* trustworthy in production

ARVIS starts from a different premise:

```text
input
→ governed cognition
→ admissibility controls
→ canonical state
→ verifiable IR
→ authorized execution
→ timeline commitment
```

Outputs are not assumed valid.

**They must become allowed to exist.**

---

## Quick Start

Install from source (works today):

```bash
git clone https://github.com/Julien-Lefauconnier/arvis
cd arvis
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

PyPI (`pip install arvis`) is planned once the alpha stabilizes.

```python
from arvis import ArvisEngine

engine = ArvisEngine()

result = engine.ask("Should this high-risk transaction be approved?")

print(result.summary())
```

Advanced runtime access:

```python
from arvis import CognitiveOS

os = CognitiveOS()

result = os.run(
    user_id="demo",
    cognitive_input={
        "risk": 0.92,
        "action": "wire_transfer",
    }
)

print(result.summary())
```

High-risk input is refused before execution:

```text
Status        : BLOCKED
Approval Need : YES
Commitment    : 8642d95cfdb73c16...
```

> Note (0.1.0-alpha): the gate grades an explicit top-level `risk` scalar —
> low → ALLOWED, medium → REQUIRES_CONFIRMATION, high → BLOCKED (see
> `examples/09_multi_run_batch.py`). This risk policy applies only to an
> explicit `risk` field; a bare text prompt is governed with a minimal
> projection (REQUIRES_CONFIRMATION), not a full natural-language projection.

---

## Public API Levels

ARVIS exposes two entrypoints:

| API | Intended Use |
|-----|--------------|
| ArvisEngine | Recommended developer-facing API |
| CognitiveOS | Advanced low-level runtime control |

For most integrations, start with:

```python
from arvis import ArvisEngine
```

### When to use what?

- Use **ArvisEngine** for application-level integrations
- Use **CognitiveOS** when you need:
  - deterministic replay
  - IR control
  - pipeline customization

---

## What ARVIS Enables

ARVIS is designed for teams building:

* enterprise copilots
* regulated AI workflows
* financial decision systems
* legal / compliance systems
* secure internal AI tools
* autonomous workflows with controls
* long-memory assistants
* high-trust AI infrastructure

In these environments, output quality alone is not enough.

Systems must be:

* explainable
* reproducible
* governable
* observable
* safe under uncertainty

---

## Core Capabilities

### Deterministic Cognition

Same input + same state + same policy = same result.

### Replayable Decisions

Runs can be replayed and verified.

### Governed Outputs

Unsafe or invalid decisions can be blocked before execution.

### Controlled Tool Use

External tools and side-effects run behind authorization boundaries.

### Explicit Uncertainty

Risk, ambiguity, conflict, and instability become system signals.

### Canonical IR

Every run can emit a structured machine-auditable representation.

### Timeline Integrity

Decisions can be linked to verifiable commitments.

### Runtime Observability

Internal cognition remains inspectable in production.

---

## Architecture Snapshot

```text
Scheduler Tick
  → Select Process
  → Run Cognitive Pipeline
  → Build Cognitive State
  → Policy / Admissibility Gate
  → Export IR
  → Optional Authorized Execution
  → Timeline Commit
```

---

## Separation of Concerns

| Layer     | Responsibility             |
| --------- | -------------------------- |
| Pipeline  | Cognition                  |
| Gate      | Decision admissibility     |
| Runtime   | Scheduling / orchestration |
| Memory    | Governed state influence   |
| IR        | Structured export          |
| Execution | Side-effects / tools       |
| Timeline  | Integrity / commitments    |
| Reflexive | Read-only self-observation |

---

## Why Teams Choose ARVIS

Because modern AI systems increasingly need:

* controls before execution
* replay after incidents
* audit trails for regulators
* safe tool usage
* deterministic workflows
* bounded autonomy
* trustable infrastructure

ARVIS addresses these requirements natively.

---

## Validation

ARVIS is validated like infrastructure.

Current suite includes:

* 1700+ passing tests
* unit tests
* integration tests
* deterministic replay verification
* adversarial scenarios
* scheduler fairness tests
* hashchain integrity tests
* mathematical invariants
* runtime robustness checks

---

## Examples

Run ready-to-use examples:

```bash
python examples/00_quickstart_engine.py
```

Included examples:

0. ArvisEngine quickstart
1. Gate refusal
2. Deterministic replay
3. IR export
4. Human approval
5. Tool governance
6. Finance risk screening
8. Timeline audit trail
9. Batch decision engine
10. Runtime inspection

See: `examples/README.md`

---

## Documentation

Start here:

* `docs/OVERVIEW.md`
* `docs/WHY_ARVIS.md`
* `docs/ARCHITECTURE.md`
* `docs/PIPELINE.md`
* `docs/IR.md`
* `docs/REFLEXIVE.md`
* `docs/standard/`
* `docs/math/`

---

## What ARVIS Does Not Claim

ARVIS does **not** promise:

* universal truth
* AGI magic
* perfect reasoning
* correctness outside assumptions
* optimality in all environments

ARVIS is about **trustworthy operation under constraints**.

---

## Known Limitations (0.1.0-alpha)

This is an early alpha of a deterministic cognitive kernel. What is stable,
experimental, and out of scope for 0.1:

**Stable (documented, tested):**

* governed decision pipeline and admissibility gate
* graded risk gate for an explicit top-level `risk` scalar
  (low → ALLOWED, medium → REQUIRES_CONFIRMATION, high → BLOCKED)
* deterministic, replayable IR (projection / validity / stability / adaptive /
  tools axes exposed in the public view) and timeline commitment
* syscall boundary for external effects, including a governed `llm.generate`
  path wired end to end
* tool authorization boundary (per-spec risk budget)
* typed runtime error model

**Experimental (present, not part of the stable public API):**

* long-term memory
* conversation orchestration
* natural-language input surface — a bare text prompt is governed with a
  *minimal* projection (REQUIRES_CONFIRMATION), not a full cognitive projection
* real LLM providers — the governed adapter path is wired end to end, but the
  bundled provider is a deterministic stub; production providers must be
  configured via the adapter registry

**Out of scope for 0.1:**

* the full cognitive projection Pi (the 0.1 projection is partial and
  certification-oriented; sparse inputs receive a minimal certificate)
* risk gating beyond an explicit top-level `risk` scalar (nested signals,
  structured tool requests, and free text do not yet drive a full projection)
* general formal guarantees over arbitrary LLM behavior
* a frozen public API surface

Formal guarantees apply only to the documented projected domains and their
assumptions.

---

## Versioning

ARVIS tracks three distinct version axes, each honestly labeled:

| Axis | Value | Meaning |
|------|-------|---------|
| Package version | `0.1.0a5` | the distributed artifact (PEP 440) |
| API version | `0.1` | the public Python API contract (not yet stable) |
| Standard version | `draft-v1` | the ARVIS decision / IR specification |

---

## Project Status

**`0.1.0-alpha` (preview)** — actively developed with a validation-first
engineering approach. The public API is not yet stable.

---

## Positioning

```text
Most AI systems try to generate outputs.
ARVIS governs whether outputs are allowed to exist.
```
