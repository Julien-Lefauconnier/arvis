# Canonical Cognitive State

## Definition

The Cognitive State is the **canonical internal representation of the system after a full cognitive execution**.

It is:

- deterministic
- normalized
- contract-validated
- complete (no semantic loss from execution context)

IMPORTANT:

> The Cognitive State is NOT the pipeline output.
> It is a **post-processed canonical aggregation** of the full cognitive context.

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
```

In implementation:

```python
ctx.cognitive_state = CognitiveStateBuilder.from_context(ctx)
CognitiveStateContract.validate(ctx.cognitive_state)
```

---

## Role in the System

The Cognitive State is the central canonical bridge between:

- cognitive execution (pipeline)
- observability and stability metrics
- IR export layer

It ensures that:

- all signals are normalized
- all values are bounded and valid
- no implicit state remains in the system

---

## Components

The Cognitive State aggregates:

### 1. Decision Context

- decision result
- confirmation state
- execution feasibility

### 2. Stability & Risk Signals

- system tension
- stability projection
- predictive signals
- risk indicators

### 3. Control State

- control snapshot
- exploration parameters
- regime

### 4. Observability Outputs

- predictive snapshot
- multi-horizon projections
- global stability
- symbolic state

### 5. Execution Context
- executable intent
- action decision
- pending actions

---

## Properties

The Cognitive State guarantees:

- deterministic structure
- bounded values
- explicit signal representation
- no hidden computation state
- compatibility with contract validation

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

If validation fails:

- the state is discarded
- the system falls back safely

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

---

## Invariants

The Cognitive State enforces:

- determinism
- no hidden state
- no invalid signals
- no out-of-bound values
- consistency with pipeline outputs
- consistency with observability projections

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

---

## Important Distinction

The Cognitive State is NOT:

- a decision
- a response
- a signal registry
- a user-facing object

It is:

    the canonical internal snapshot of cognition after validation and stabilization.