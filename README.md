# ARVIS

**Cognitive OS governed by a formal stability law**

> Not a model. Not an agent.  
> A **deterministic cognitive execution system**.

---

## 🔥 Core Principle

ARVIS does not generate decisions.

It determines whether a decision is **allowed to exist**.

---

## 🧩 Formal Foundation

ARVIS is grounded in a formally proven stability core.

→ Read the full specification:
- **[ARVIS Stability Core Specification](./ARVIS_STABILITY_CORE_SPECIFICATIONS.md)**

This document defines the fundamental stability condition (T1):

    log J / τ_d + log(1 - κ_eff) < 0

→ which governs all admissible system behaviors.

---

### Theory ↔ Implementation Mapping

The correspondence between the formal model and the production system is defined here:

- **[Theory ↔ System Mapping](./docs/architecture/MAPPING_ARVIS_SPECIFICATIONS_IMPLEMENTATION.md)**

This mapping ensures:

- traceability of all mathematical constructs
- runtime verifiability of theoretical assumptions
- strict separation between proven guarantees and system extensions

---

## 🧠 What Makes ARVIS Different

- Deterministic cognitive pipeline (no hidden reasoning)
- Stability-constrained decision space
- No decision without prior validation
- Fully replayable cognition (hash-chained timeline) — built on the [Veramem Kernel](https://github.com/Julien-Lefauconnier/kernel)
- Strict typing (mypy --strict enforced)

---

## ⚡ In One Sentence

> ARVIS turns cognition into a **constrained system with guarantees**, not a probabilistic process.

---

## Quick Glossary

- Bundle: immutable snapshot of cognitive state
- Core: scientific modeling (risk, drift, stability)
- Gate: stability check before execution
- Timeline: append-only, hash-chained memory
- ZKCS: zero-knowledge cognitive separation (data vs reasoning)

---

## Core Idea

Most systems try to generate decisions.

ARVIS does something fundamentally different:

> It determines whether a decision is **allowed to exist**.

A decision in ARVIS is:

- constructed from explicit state (bundle)
- evaluated through scientific modeling (core)
- constrained by control and stability
- gated before execution

If constraints are not satisfied:

→ the decision does not exist

---

#### Badges

![CI](https://github.com/Julien-Lefauconnier/arvis/actions/workflows/CI.yml/badge.svg)
![Coverage](https://codecov.io/gh/Julien-Lefauconnier/arvis/branch/main/graph/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-Apache%202.0-blue)
![Mypy](https://img.shields.io/badge/mypy-strict-blue)
![Ruff](https://img.shields.io/badge/lint-ruff-black)
![Status](https://img.shields.io/badge/status-research--grade-purple)

---

## Current Status

ARVIS is a **formally constrained cognitive system**.
It is a **fully operational cognitive kernel** ready for research, safety evaluation, and extension.  
We welcome collaborators, reviewers, and early adopters.

- 630+ tests (unit, integration, adversarial)
- 95%+ code coverage
- deterministic execution pipeline
- formal invariants enforced at runtime
- adversarial robustness validation
- replayable, hash-chained cognition timeline

This repository represents a **production-grade cognitive system architecture**.

---

## Installation & Quickstart

```bash
git clone https://github.com/Julien-Lefauconnier/arvis.git
cd arvis
pip install -e .
```

```python
from arvis.api import CognitiveOS

os = CognitiveOS()
result = os.run(
  user_id="test-user",
  cognitive_input="Should I approve this financial transaction?"
)

print(result.decision)          # → structured decision
print(result.stability.score)   # → 0.0–1.0 stability score
print(result.has_trace)         # → true
```

Output example:

```json
{
  "decision": "DENY – high collapse risk detected",
  "stability": { "score": 0.42, "risk": 0.78, "regime": "unstable" },
  "trace_id": "trc_abc123...",
  "timeline_hash": "sha256:xyz..."
}
```

See examples/ for more scenarios.

---

## What is ARVIS?

ARVIS is a **Cognitive Operating System (Cognitive OS)**.

It enforces **whether a decision is allowed to exist, and under which conditions it can be executed**   
under strict mathematical, structural, and temporal constraints.

> Most AI systems optimize outputs.  
> ARVIS enforces **the conditions under which outputs are allowed to exist**.

---

## The Problem

Modern AI systems:

- rely on unstable heuristics
- operate on untyped scalar values (floats)
- lack formal guarantees
- cannot be audited or replayed reliably
- degrade silently under distribution shift


They are powerful — but **structurally unsafe**.

---

## Why Now

As AI systems become more autonomous and widely deployed,
the absence of formal guarantees becomes a critical risk.

ARVIS addresses this gap by introducing:

- stability constraints before execution
- auditable decision pipelines
- deterministic cognitive flows

It shifts AI from probabilistic output generation
to **constrained cognitive systems**.

---

## What ARVIS is NOT

- not a machine learning model
- not a prompt framework
- not an agent toolkit
- not a heuristic decision engine

ARVIS does not generate intelligence.

It **constrains intelligence**.

---

## Formal Guarantees

### Fundamental Constraint

All ARVIS decisions must satisfy the stability condition (T1).

A decision that violates this condition is:

→ mathematically invalid  
→ structurally impossible to execute

ARVIS enforces system-level properties:

- Deterministic cognition pipeline
- No uncontrolled side effects
- Stability-constrained decision space
- Immutable signal semantics
- Explicit uncertainty modeling
- Replayable execution with identical results
- Explicit separation between state, computation, and control
- No decision without prior stability validation

A decision that violates constraints:

→ **is structurally impossible to execute**

---

## The ARVIS Approach

ARVIS introduces a new paradigm:

```text
cognition → constrained system → controlled decision
```
Not:
```text
input → model → output
```

---

## Cognitive Architecture Model

ARVIS separates cognition into three strictly isolated components:

### Cognitive Bundle (State)

A deterministic, immutable snapshot of cognitive state.

- no reasoning
- no execution
- complete explicit representation

---

### Cognitive Core (Scientific Modeling)

A pure computation layer that evaluates system dynamics:

- collapse risk
- drift
- regime signals

It does not decide.  
It measures.

---

### Cognitive Pipeline (Execution Protocol)

A deterministic sequence of stages that:

- orchestrates cognition
- applies control logic
- enforces constraints
- gates execution

---

This separation ensures:

→ no hidden reasoning  
→ no implicit state  
→ no uncontrolled decisions

## A True Cognitive OS

ARVIS is not a library.

It is a system layer, structured like an operating system:

### Kernel

Deterministic execution pipeline → no uncontrolled side effects

### Cognition Layer

Decision logic under constraints → conflict, uncertainty, prediction

### Stability Layer (Mathematical Core)

Control theory + probabilistic bounds → guarantees before execution

### Timeline Layer

Immutable, hash-chained memory → replayable cognition

### API Layer

Stable, versioned contract → auditable outputs

(The public repository exposes the stable and auditable surface of the system.
Additional components are under active research and development.)

---

## Mathematical Foundation

ARVIS is grounded in a formally specified Lyapunov stability core (see Stability Core Specification).

No decision exists outside this stability condition.

- Lyapunov stability theory (composite + switching)
- runtime stability enforcement (multi-axial fusion)
- probabilistic risk bounds (Hoeffding-style)
- multi-horizon predictive modeling
- regime detection (stable / unstable / collapse)
- adaptive control (IRG-based)

No decision exists outside a stability proof context

No decision exists without passing a runtime stability enforcement layer.

---

## Signal-Based Cognition

ARVIS replaces raw numerical reasoning with typed, constrained signals:

```text
float → signal → contract → decision
```

Core primitives:

- RiskSignal
- UncertaintySignal
- DriftSignal

Properties:

- normalized [0,1]
- immutable
- semantically constrained
- composable

---

## Why this matters

This removes:

- magic thresholds
- implicit heuristics
- silent instability
- non-interpretable decisions

---

## Cognitive Execution Pipeline

Every decision follows a strict, enforced pipeline:

1. Decision bootstrap
2. Context integration
3. Bundle construction
4. Conflict extraction
5. Scientific modeling (core)
6. Regime & temporal evaluation
7. Adaptive control
8. Stability gating (Lyapunov)
9. Confirmation resolution
10. Execution evaluation
11. Action mapping
12. Intent formalization
13. Runtime finalization

A decision that violates constraints cannot execute

---

## Guarantees

ARVIS provides system-level guarantees:

### Determinism

Same input → same structured result

### Stability Enforcement

No unstable decision can pass

### Traceability

Every decision is fully reconstructible

### Auditability

All outputs are explainable and verifiable

### Replayability

Full timeline replay with identical behavior

---

## Timeline & Trace

### Timeline

- append-only
- hash-chained
- time-consistent (UTC + logical clocks)
- identity-bound

Decision Trace

Each decision includes:

- stability evaluation
- conflict resolution
- gating decisions
- execution outcome

(The public timeline is the visible, auditable surface; the Veramem 
system supports deep historical lineage and cross-system inheritance.)

---

## Zero-Knowledge Cognitive System (ZKCS)

ARVIS separates:

- data
- reasoning
- decision

It enables:

- reasoning without raw data exposure (ZKCS-compliant)
- safe abstraction layers
- controlled observability

(This is the exposed contract; the Veramem stack extends ZKCS to full 
encrypted cognitive pipelines.)

---

## What ARVIS Enables

ARVIS is a foundation for:

- auditable AI systems
- governable cognition
- safe long-term memory systems
- deterministic AI pipelines
- high-reliability decision systems
- AI systems under formal constraints

(The public API is the stable interface; the full Veramem system already 
supports production-grade governance, reflexive self-modeling, 
and multi-agent coordination.)

---

## Public API (Stable Contract)

```python
from arvis.api import CognitiveOS

os = CognitiveOS()

result = os.run(
  user_id="test-user",
  cognitive_input="Should I approve this financial transaction?"
)
```

---

## Output Contract

```json
{
  "version": "1.0.0",
  "fingerprint": "<sha256>",
  "decision": "...",
  "stability": {
    "score": 0.95,
    "risk": 0.1,
    "regime": "stable"
  },
  "trace_id": "...",
  "timeline_hash": "...",
  "has_trace": true,
  "has_timeline": true
}
```

---

## System Properties

- immutable state snapshots
- no hidden side effects
- no implicit reasoning
- contract-enforced pipeline
- explicit uncertainty handling

---

## Testing & Validation

- 630+ tests

- invariant validation (kernel-level)

- adversarial test suite:
  - chaos injection
  - conflict stress tests
  - pipeline adversarial scenarios
  - timeline tampering resistance

- property-based validation (Hypothesis)
- contract enforcement tests (API + kernel)


  This is not "tested code".
  
  This is a **validated cognitive system**.

---

## Architectural Properties

- Strict layer separation (kernel / cognition / math / timeline)
- No circular dependencies
- No implicit state mutation
- Explicit signal flow only
- Fully typed cognitive primitives

The system is designed to be:

→ analyzable  
→ verifiable  
→ extensible without breaking invariants

---

## Research & Ecosystem

Kernel (low-level primitives): https://github.com/Julien-Lefauconnier/kernel
→ Provides the append-only, hash-chained timeline foundation with deterministic behavior, temporal integrity, and optional cryptographic attestation (HMAC-SHA256 / Ed25519).

Veramem Research Lab: https://github.com/Julien-Lefauconnier/arvis-cognition
→ Provides the public research materials, experiments, results pusblished by the Veramem Research Lab

arvis (this repo): Cognitive OS specification + contracts + interfaces

The public repositories are stable surface layers of a much larger private system under active development.

---

## Roadmap

- [ ] Governance layer (normative & ethical constraints)
- [ ] Full uncertainty distributions & multi-frame handling
- [ ] Multi-agent cognitive coordination under shared timeline
- [ ] Encrypted & ZK-friendly cognitive pipelines
- [ ] Cryptographic verifiable execution proofs
- [ ] Distributed cognitive nodes with consensus

---

## Standardization

ARVIS is evolving into a formal standard:

→ Read the current draft: **[ARVIS Standard v1](docs/ARVIS_STANDARD_V1.md)**

---

## Status

Standardization phase

- architecture stable
- contracts stabilizing
- API nearing freeze

---

## Final Statement

ARVIS does not try to build smarter AI.

It builds:

  systems where decisions are allowed to exist 
  only if they satisfy formal constraints, stability conditions, and execution safety