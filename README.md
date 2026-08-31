# ARVIS

**The Cognitive Operating System for Governed AI Systems**

> Python 3.11+ • Deterministic • Replayable • Governed • Auditable

> **Status: `0.1.0b4` (beta).** The public surface (`arvis.__all__` and the
> stable `host_api` modules) is stabilized, versioned, and covered by the
> deprecation policy in `VERSIONING.md`: removals or type changes require a
> version bump and a changelog entry.
> The projection layer is partial, LLM governance is mock-first, and formal
> guarantees apply only to the documented projected domains. See
> [Known Limitations](#known-limitations-010-beta).

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

Install the beta from PyPI:

```bash
pip install arvis
```

Or install from source for development:

```bash
git clone https://github.com/Julien-Lefauconnier/arvis
cd arvis
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the canonical local quality gate with the same pinned tools and security
threshold used by CI:

```bash
bash scripts/run_quality_gate.sh
```

The security-only slice is available as
`bash scripts/run_quality_gate.sh security`; Bandit fails on medium- or
high-severity findings.

```python
from arvis import ArvisEngine

engine = ArvisEngine()

result = engine.ask("Should this high-risk transaction be approved?")

print(result.explain())
```

Output (deterministic; the commitment hash is stable for identical input):

```text
Status         : REQUIRES_CONFIRMATION
Approval Need  : YES
Reason         : execution_blocked
Commitment     : de29cac2ee667de9...
Trace          : Available
```

A bare text prompt is governed with a minimal projection, so it lands in
`REQUIRES_CONFIRMATION`: the engine has no basis to allow it and refuses
to execute it silently (see the note below).

Advanced runtime access:

```python
from arvis import CognitiveOS

os = CognitiveOS()

result = os.run(
    user_id="demo",
    cognitive_input={"risk": 0.92},
)

print(result.explain())
```

High-risk input is refused before execution:

```text
Status         : BLOCKED
Approval Need  : NO
Reason         : execution_blocked
Commitment     : b94e25dea93a541e...
Trace          : Available
```

`summary()` gives the one-line form. The measured axes and the
caller-declared assertion are deliberately distinct: `Stability`,
`Risk` and `Regime` are what the engine's contraction monitor measured
about this run's cognition (first turn: `warmup`), while
`DeclaredRisk` is the untrusted scalar the caller asserted, and only
the declared-risk gate acts on it:

```text
Decision=ActionDecision(allowed=False, ...) | Stability=0.85 | Risk=0.00 | Regime=warmup | DeclaredRisk=0.92
```

> Note (0.1.0-beta): the gate grades an explicit finite top-level `risk`
> scalar with two documented thresholds (`arvis/kernel/gate/input_risk.py`):
> `risk < 0.4` → ALLOWED, `0.4 <= risk < 0.8` → REQUIRES_CONFIRMATION,
> `risk >= 0.8` → BLOCKED. Two preconditions apply:
>
> 1. **Pure payload.** Grading (and therefore the ALLOWED band) applies only
>    to a payload whose single key is `risk` (`{"risk": 0.3}`). A mixed
>    payload (`{"risk": 0.3, "action": ...}`) carries content: the declared
>    risk may only harden the verdict of that content, never relax it, so a
>    mixed payload is governed by the projection verdict (BLOCKED for
>    unprojected content in this beta).
> 2. **Graded mode.** The default (`local`) profile grades; the `production`
>    profile sets the input-risk gate to *harden-only*, where a declared
>    risk never unlocks execution and every band is refused. See
>    [Runtime profiles](#runtime-profiles).
>
> `NaN` and infinities fail closed to BLOCKED. A bare text prompt is
> governed with a minimal projection (REQUIRES_CONFIRMATION), not a full
> natural-language projection.

### Engine lifecycle

One engine executes one governed run at a time; an engine instance is not
thread-safe. The documented lifecycle is one instance per governed turn,
discarded afterwards (`docs/architecture/RUNTIME_LIFECYCLE.md`). Sequential
reuse of one instance on a single thread works and is exercised by the
isolation tests, but it accumulates state without bound (no TTL, no
eviction) and is not the recommended pattern; concurrent reuse is forbidden.
Parallelism belongs to the host, by instantiation: engines in the same
process are isolated by construction. The guarantee is tested in
`tests/api/test_multi_instance_isolation.py`, the one-instance-per-turn
factory pattern is shown in `examples/09_multi_engine_hosting.py`, and a
contract test keeps every example on that pattern
(`tests/contracts/test_examples_lifecycle.py`).

---

## Runtime profiles

`CognitiveOSConfig` ships two named profiles, and the difference is not
cosmetic:

| Posture | `local` (default) | `production` |
|---|---|---|
| Input-risk gate | graded (three bands above) | **harden-only: every declared risk is refused** |
| Tool gates | permissive default | deny-by-default |
| Tool registry | open | frozen |
| Host runtime controls | accepted | rejected |
| Global stability action | monitor | confirm |
| Switching envelope | monitor | enforce |

The default profile is a *development* posture for embedding and
iteration. `CognitiveOSConfig.production()` is the deployment posture: in
this beta it refuses every input the partial projection cannot certify,
including a pure `{"risk": 0.0}` payload. That is deliberate fail-closed
behavior, not a bug, and it means the graded three-band flow shown above
is a property of the default profile only.

```python
from arvis import CognitiveOS, CognitiveOSConfig

os = CognitiveOS(config=CognitiveOSConfig.production())
```

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

Each authorized tool receives a canonical frozen payload and an immutable
`AuthorizedEffectContext`; it never receives the mutable cognitive pipeline
context. The syscall boundary compares the current trusted identity with the
sealed principal, tenant, authentication, service, session, process and run
bindings before committing an intent. See the normative
[governed effect path](docs/architecture/EFFECT_PATH.md) and the
[tool authoring guide](docs/tools/TOOL_AUTHORING_GUIDE.md).

### Explicit Uncertainty

Risk, ambiguity, conflict, and instability become system signals.

### Canonical IR

Every run can emit a structured machine-auditable representation.

### Timeline Integrity

Decisions can be linked to verifiable commitments.

### Runtime Observability

Internal cognition remains inspectable in production.

---

## Where ARVIS Fits

ARVIS sits between an application's AI-generated proposals and its governed
tools. The host still owns identity, business rules, memory, models, storage,
queues and external providers.

Start with:

* [Reference architecture: sovereign, governed AI assistant](https://github.com/Julien-Lefauconnier/arvis/blob/main/docs/architecture/REFERENCE_ASSISTANT_ARCHITECTURE.md)
* [Runnable governed-assistant example](https://github.com/Julien-Lefauconnier/arvis/blob/main/examples/11_governed_assistant.py)
* [VeraMem integration pattern](https://github.com/Julien-Lefauconnier/arvis/blob/main/docs/integration/VERAMEM_INTEGRATION_PATTERN.md)

The architecture is implementation-neutral. VeraMem is the author's own
application of the pattern (not an independent adoption), and neither a
dependency nor a required deployment stack.

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

* 3000+ passing tests (unit, integration, property-based)
* deterministic replay verification (full-IR comparison)
* adversarial regression tests pinning reproduced attack vectors
  (`tests/adversarial/test_campaign_audit_regression*.py`, VFS scope
  campaigns)
* hashchain integrity tests
* gate safety-ordering and bounded-recovery properties
  (`tests/math/gate/test_gate_safety_ordering.py`)
* runtime robustness checks

What the suite does **not** yet establish, honestly: scheduler
*fairness* is only covered by single-tick priority tests (no starvation
or bounded-wait property), and the Lyapunov decrease property is
asserted at unit level and on threaded-state runs, not yet as a
closed-loop property over long adversarial trajectories.

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
9. Multi-engine hosting (one engine per governed turn)
10. Runtime inspection
11. Governed-assistant reference integration

See: `examples/README.md`

---

## Documentation

Start here:

* `docs/OVERVIEW.md`
* `docs/WHY_ARVIS.md`
* `docs/ARCHITECTURE.md`
* `docs/architecture/REFERENCE_ASSISTANT_ARCHITECTURE.md`
* `docs/integration/VERAMEM_INTEGRATION_PATTERN.md`
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

## Known Limitations (0.1.0-beta)

This is a beta of a deterministic cognitive kernel. What is stable,
experimental, and out of scope for the 0.1 series:

**Stable (documented, tested):**

* governed decision pipeline and admissibility gate
* graded risk gate for an explicit top-level `risk` scalar, default
  profile, pure payload (`< 0.4` → ALLOWED, `0.4`–`0.8` →
  REQUIRES_CONFIRMATION, `>= 0.8` → BLOCKED; see the Quick Start note)
* deterministic, replayable IR (projection / validity / stability / adaptive /
  tools axes exposed in the public view) and timeline commitment
* syscall boundary for external effects, including a governed `llm.generate`
  path wired end to end
* tool authorization boundary (per-spec risk budget)
* sealed tool effect context and receipt-activated single-use capabilities
* typed runtime error model

**Behavioral caveats (know these before deploying):**

* the **`production` profile refuses everything** the partial projection
  cannot certify: with `input_risk_mode = "harden_only"`, every declared
  risk value, including `0.0`, is BLOCKED. The graded three-band gate is
  a property of the default (`local`) profile.
* the **contraction monitor is the default core model**: every governed
  run measures a Lyapunov state, its energy V, a drift score, a PAC
  risk ceiling and an empirical regime (`ContractionMonitorCore`;
  `core_model=None` opts out). The measured axes never act on a
  caller-declared risk scalar, which stays governed by the input-risk
  gate alone. **Trajectory properties need threaded state**: the
  engine is one-turn by design, so delta-V (and the Lyapunov gate's
  trajectory branch) only become live when the host threads the
  replayable `scientific_state` between turns
  (`run(..., extra={"scientific_state": previous})`, read back from
  `extra["scientific_state_next"]`). A first, unthreaded turn is
  conservative by construction.
* **stability axes are reported only when measured**: `summary()` and
  the stability view return `n/a`/`null` for axes the run did not
  compute, rather than zeros (`stability_score` is `1 - V`, the
  complement of the measured energy).

**Experimental (present, not part of the stable public API):**

* long-term memory
* conversation orchestration
* natural-language input surface: a bare text prompt is governed with a
  *minimal* projection (REQUIRES_CONFIRMATION), not a full cognitive projection
* real LLM providers: the governed adapter path is wired end to end, but the
  bundled provider is a deterministic stub; production providers must be
  configured via the adapter registry

**Out of scope for 0.1:**

* the full cognitive projection Pi (the 0.1 projection is partial and
  certification-oriented; sparse inputs receive a minimal certificate)
* risk gating beyond an explicit top-level `risk` scalar (nested signals,
  structured tool requests, and free text do not yet drive a full projection)
* general formal guarantees over arbitrary LLM behavior
* distributed registry, confirmation and idempotency coordination

Formal guarantees apply only to the documented projected domains and their
assumptions.

---

## Versioning

ARVIS tracks three distinct version axes, each honestly labeled:

| Axis | Value | Meaning |
|------|-------|---------|
| Package version | `0.1.0b4` | the distributed artifact (PEP 440) |
| API version | `0.1` | stable within the beta series under `VERSIONING.md` |
| Standard version | `draft-v1` | the ARVIS decision / IR specification |

---

## Project Status

**`0.1.0b4` (beta)**: actively developed with a validation-first engineering
approach. The documented public and host surfaces are stable within the beta
series; experimental internals and the draft standard may still evolve.

---

## Positioning

```text
Most AI systems try to generate outputs.
ARVIS governs whether outputs are allowed to exist.
```
