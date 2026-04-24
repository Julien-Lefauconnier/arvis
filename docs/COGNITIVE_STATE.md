# Canonical Cognitive State

## Definition

The Cognitive State is the **canonical internal representation of the system after a full cognitive execution**.

It is:

- deterministic
- normalized
- contract-validated
- complete (no semantic loss from execution context)
- stable across runtime refactors

IMPORTANT:

> The Cognitive State is NOT the pipeline output.
> It is a **post-processed canonical aggregation** of the full cognitive context.

It converts transient runtime artifacts into a deterministic internal truth model.

---

## Construction

The Cognitive State is built AFTER pipeline execution and post-processing:

```text
Pipeline execution
→ Observability computation
→ Stability projection
→ Context aggregation
→ CognitiveStateBuilder
→ CognitiveStateContract validation
→ Canonical state attached to result context
```

In implementation:

```python
ctx.cognitive_state = CognitiveStateBuilder.from_context(ctx)
CognitiveStateContract.validate(ctx.cognitive_state)
```

The builder is responsible for normalization and field aggregation.  
The contract is responsible for admissibility and integrity.

---

## Role in the System

The Cognitive State is the central canonical bridge between:

- cognitive execution (pipeline)
- observability and stability metrics
- IR export layer
- replay verification
- reflexive inspection

It ensures that:

- all signals are normalized
- all values are bounded and valid
- no implicit state remains in the system
- downstream layers consume one stable contract instead of scattered runtime fields

---

## Components

The Cognitive State aggregates:

### 1. Decision Context

- decision result
- confirmation state
- execution feasibility
- gate verdict metadata

### 2. Stability & Risk Signals

- system tension
- stability projection
- predictive signals
- risk indicators
- validity envelope status

### 3. Control State

- control snapshot
- exploration parameters
- regime
- adaptive modulation state

### 4. Observability Outputs

- predictive snapshot
- multi-horizon projections
- global stability
- symbolic state
- trend / drift summaries

### 5. Execution Context
- executable intent
- action decision
- pending actions
- action admissibility state

### 6. Timeline / Trace Anchors

- execution identifiers
- deterministic commitments
- replay references

---

## Properties

The Cognitive State guarantees:

- deterministic structure
- bounded values
- explicit signal representation
- no hidden computation state
- compatibility with contract validation
- stable semantics across implementations

---

## Contract Validation

The Cognitive State MUST pass a strict contract:

```python
CognitiveStateContract.validate(state)
```

This enforces:

- type correctness
- signal bounds
- structural integrity
- absence of invalid values
- no NaN / corrupted numeric states
- required field consistency

If validation fails:

- the state is discarded
- the system falls back safely
- invalid state is never exported downstream

---

## Relation to IR

The Cognitive State is NOT exposed directly.

It is transformed into IR:

```python
StateIRAdapter.from_state(ctx.cognitive_state)
```

### Key distinction:

| Layer          | Role                            |
| -------------- | ------------------------------- |
| CognitiveState | internal canonical state        |
| IR             | external machine representation |

The IR:

- may omit internal fields
- may reorganize structure
- is optimized for portability
- is versioned independently from runtime internals

The Cognitive State exists for correctness.  
The IR exists for interoperability.

---

## Invariants

The Cognitive State enforces:

- determinism
- no hidden state
- no invalid signals
- no out-of-bound values
- consistency with pipeline outputs
- consistency with observability projections
- consistency with contract schemas
- deterministic rebuild under identical inputs

---

## Design Principle

The Cognitive State is the single source of truth inside ARVIS.

Everything else is derived from it:

```text
CognitiveState
→ IR
→ Canonical Signals
→ External systems
```

All downstream representations must derive from this layer, never bypass it.

---

## Important Distinction

The Cognitive State is NOT:

- a decision
- a response
- a signal registry
- a user-facing object
- a mutable working memory store
- a transport contract

It is:

    the canonical internal snapshot of cognition after validation and stabilization.

---

## Why It Exists

Without a canonical state, systems drift into:

- duplicated runtime fields
- hidden coupling
- inconsistent exports
- replay ambiguity
- brittle integrations

ARVIS uses CognitiveState to prevent those failure modes.

---

## One-Line Summary

Pipeline execution computes cognition. CognitiveState freezes it into canonical truth.