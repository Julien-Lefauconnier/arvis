# ARVIS Intermediate Representation (IR)

## Version

Current version: `arvis-ir.v1`

---

## Definition

The IR is the **canonical, deterministic machine representation** of a cognitive execution in ARVIS.

It is not a raw export.

It is a **normalized, validated, and hashed representation** of the cognitive process.

IMPORTANT:

The IR is NOT a signal system.

It is an **expressive, information-complete representation** of cognition.

It is designed for:

- traceability
- replay
- auditability
- structured interpretation

It is NOT constrained by external canonical signal registries.

IMPORTANT:

The IR represents **cognitive evaluation**, not the final user response.

- It contains validated intent, state, and decision signals
- It does NOT contain conversational realization or generated outputs

Response generation occurs in the Conversation & Realization layers.

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

## Top-level structure (simplified view)

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
serialized = to_canonical_dict(...)
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
- Deterministic transformation from finalized cognitive context (including post-pipeline observability and projection layers)
- Stable normalization
- Stable hashing
- Replay consistency
- Information completeness (no semantic loss from pipeline output)

---

## Replay

The IR can be used to replay execution:

```python
pipeline.run_from_ir(ir)
```

Replay mode:

- deterministic
- side-effect minimized (but may depend on runtime configuration)
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

NOTE:

For interoperability with **external signal-based systems** (e.g. Veramem Kernel),
the IR MUST be transformed through a dedicated projection layer:

→ Kernel Adapter (Canonical Projection Layer)

This transformation:

- is deterministic
- is rule-based
- is lossy (information may be reduced to match canonical constraints)
- does NOT belong to the IR itself

---

## Design Principle

The IR is the external contract of ARVIS.

It connects:

- the internal CognitiveState
- the pipeline execution
- external consumers

It is:

  stable, deterministic, and machine-verifiable

---

---

## IR vs Canonical Signals (CRITICAL DISTINCTION)

ARVIS distinguishes between:

### IR (Intermediate Representation)

- expressive
- complete
- information-rich
- internal canonical contract

### Canonical Signals (External Systems)

- constrained
- registry-bound
- reduced representation
- interoperability-focused

The transformation:

```text
IR → Canonical Signals
```

is:

- deterministic
- rule-based
- external to the IR specification

This ensures:

- IR remains stable and expressive
- external integrations remain compatible with strict canonical systems