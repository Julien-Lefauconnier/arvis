# ARVIS Intermediate Representation (IR)

## Version

Current version: `arvis-ir.v1`

---

## Definition

The IR is the **canonical, deterministic machine representation** of a cognitive execution in ARVIS.

It is not a raw export.

It is a **normalized, validated, and hashed representation** of the cognitive process.

---

## IR Construction Pipeline

The IR is built through a canonical pipeline:

```text
CognitiveIRBuilder
→ CognitiveIRNormalizer
→ CognitiveIRValidator
→ CognitiveIRSerializer
→ CognitiveIRHasher
→ CognitiveIREnvelope
```

This ensures:

- deterministic structure
- order-invariant normalization
- validation before exposure
- stable hashing
- replayability

---

## Top-Level Structure (v1)

The IR is represented by the CognitiveIR object:

```python
CognitiveIR(
    input=...,
    context=...,
    decision=...,
    state=...,
    gate=...,
    stability=...,
    adaptive=...,
)
```

---

## Core Components

### 1. Input (CognitiveInputIR)

Represents the originating input.

Fields:

- input_id
- actor_id
- surface_kind
- intent_hint
- metadata

### 2. Context (CognitiveContextIR)

Represents execution context.

Fields:

- user_id
- session_id
- conversation_mode
- long_memory_constraints
- long_memory_preferences
- extra

### 3. Decision (CognitiveDecisionIR)

Represents structured decision semantics.

Fields include:

- decision_id
- decision_kind
- memory_intent
- reason_codes
- proposed_actions
- gaps
- conflicts
- reasoning_intents
- uncertainty_frames
- knowledge
- context_hints

### 4. State (CognitiveStateIR)

Represents the canonical cognitive state.

Derived from:

- CognitiveStateBuilder
- CognitiveStateContract

Contains normalized signals such as:

- stability
- control state
- regime
- risk indicators

### 5. Gate (CognitiveGateIR)

Represents the stability validation outcome.

Fields:

- verdict (ALLOW / REQUIRE_CONFIRMATION / ABSTAIN)
- bundle_id
- reason_codes

---

## Optional Extensions

Depending on runtime configuration, IR may include:

### Projection

- projection certificate
- domain validity

### Validity

- validity envelope

### Stability

- projected stability state
- stability statistics

### Adaptive
- adaptive control snapshot

---

## Normalization

The IR is normalized before validation:

- reason codes are sorted
- actions are ordered
- conflicts and gaps are canonicalized
- context hints are sorted

This guarantees:

  - identical semantic IR → identical normalized IR

---

## Validation

The IR is validated before serialization.

Validation enforces:

- schema integrity
- field consistency
- type correctness

---

## Serialization

The IR is serialized into a deterministic representation:

```python
serialized = CognitiveIRSerializer.serialize(ir)
```

---

## Hashing

A stable hash is computed:

```python
hash_value = CognitiveIRHasher.hash(ir)
```

Guarantees:

- identical IR → identical hash
- normalization ensures hash stability

---

## Envelope

The IR can be wrapped into a canonical envelope:

```python
CognitiveIREnvelope(
    ir=...,
    serialized=...,
    hash=...
)
```

The envelope is the portable contract.

---

## Invariants

The IR guarantees:

- Determinism
- No hidden state
- Pure transformation from pipeline output
- Stable normalization
- Stable hashing
- Replay consistency

---

## Replay

The IR can be used to replay execution:

```python
pipeline.run_from_ir(ir)
```

Replay mode:

- deterministic
- side-effect free
- used for validation and auditing

---

## Compatibility Rules

### Minor updates

- new fields allowed
- no change to existing semantics

### Major updates

- version bump required
- breaking changes documented

---

### Use Cases

- deterministic replay
- audit and compliance
- system interoperability
- LLM structured prompting
- trace verification

---

## Design Principle

The IR is the external contract of ARVIS.

It connects:

- the internal CognitiveState
- the pipeline execution
- external consumers

It is:

  stable, deterministic, and machine-verifiable