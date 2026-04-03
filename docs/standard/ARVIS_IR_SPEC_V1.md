# ARVIS Intermediate Representation Specification v1

## Status
- Version: v1
- Scope: Normative (Core)
- Component: ARVIS Core / Interface Layer

---

## 1. Purpose

The ARVIS Intermediate Representation (IR) defines the **canonical, deterministic, and versioned output** of a cognitive execution.

The IR serves as:

- the primary interface between ARVIS and external systems
- the basis for audit, replay, and compliance
- a machine-verifiable representation of a cognitive episode

Every ARVIS-compliant system MUST produce a valid IR.

---

## 2. Core Principles

### 2.1 Determinism

Given identical inputs, the IR MUST be identical:

- same structure
- same values
- same ordering

---

### 2.2 Canonicalization

The IR MUST be normalized before exposure:

- order-invariant
- stable across executions
- free of runtime artifacts

---

### 2.3 Replayability

The IR MUST allow:

- deterministic replay
- reconstruction of the decision path
- verification of constraints

---

### 2.4 Separation of Layers

The IR system is composed of distinct layers:

1. Raw IR (from pipeline)
2. Normalized IR
3. Validated IR
4. Serialized IR
5. Hashed IR
6. Envelope (portable contract)

---

## 3. Canonical IR Structure (v1)

The normative IR object is:

```yaml
CognitiveIR:
  input: CognitiveInputIR
  context: CognitiveContextIR
  decision: CognitiveDecisionIR
  state: CognitiveStateIR | null
  gate: CognitiveGateIR
  stability: StabilityIR | null
  adaptive: AdaptiveIR | null
```

---

## 4. IR Construction Pipeline

The IR MUST be built through the canonical pipeline:

```text
CognitiveIRBuilder
→ CognitiveIRNormalizer
→ CognitiveIRValidator
→ CognitiveIRSerializer
→ CognitiveIRHasher
→ CognitiveIREnvelope
```

Each step is mandatory for full compliance.

---

## 5. Component Definitions

### 5.1 Input

Represents the originating interaction.

MUST include:

- input_id
- actor_id
- surface_kind
- metadata

### 5.2 Context

Represents execution context.

MUST include:

- user_id
- session_id (if available)
- memory constraints / preferences
- execution context hints

### 5.3 Decision

Represents structured decision semantics.

MUST include:

- decision_id
- decision_kind
- memory_intent
- reason_codes
- structured decision components (actions, gaps, conflicts)

### 5.4 State

Represents canonical cognitive state.

Derived from:

- CognitiveStateBuilder
- CognitiveStateContract

MAY be null if unavailable.

### 5.5 Gate

Represents final decision validation.

MUST include:

- verdict ∈ {ALLOW, REQUIRE_CONFIRMATION, ABSTAIN}
- reason_codes

### 5.6 Stability (Optional)

Represents projected stability state.

### 5.7 Adaptive (Optional)

Represents adaptive control snapshot.

### 5.8 Tools ( Runtime Execution Layer)

Represents tool execution results associated with the cognitive episode.

Properties:
- MUST be deterministic
- MUST reflect actual runtime execution
- MUST NOT influence decision semantics

Structure:

ToolResultIR:
  tool_name: str
  success: bool
  output: Any | null
  error: str | null
  latency_ms: float | null

---

## 6. Normalization

The IR MUST be normalized before validation.

Normalization MUST ensure:

- sorted reason_codes
- deterministic ordering of collections
- stable mapping ordering
- semantic equivalence → structural equivalence

---

## 7. Validation

The IR MUST pass validation before serialization.

Validation enforces:

- schema integrity
- type correctness
- cross-field consistency

---

## 8. Serialization

The IR MUST be serialized deterministically.

Example:

```text
serialized = CognitiveIRSerializer.serialize(ir)
```

---

## 9. Hashing

The IR MUST support deterministic hashing:

```text
hash = CognitiveIRHasher.hash(ir)
```

Rules:

- identical IR → identical hash
- normalization required before hashing

---

## 10. Envelope

The IR MUST be embeddable in an envelope:

```yaml
CognitiveIREnvelope:
  ir: CognitiveIR
  serialized: string
  hash: string
```

The envelope is the portable IR contract.

---

## 11. Invariants

The IR MUST satisfy:

- no hidden state
- full determinism
- consistency between gate and decision
- reason_codes reflect triggered conditions
- normalized IR is idempotent

---

## 12. Replay Requirements

The IR MUST support replay:

```python
pipeline.run_from_ir(ir)
```

Replay MUST produce:

- identical verdict
- identical reason_codes
- identical IR after normalization

---

## 13. Compatibility Rules

### Minor updates

- new optional fields allowed
- no semantic change

### Major updates

- version bump required
- breaking changes documented

---

## 14. Compliance Requirements

An implementation is IR-compliant if:

- IR is normalized
- IR is validated
- serialization is deterministic
- hashing is stable
- replay is consistent

---

## 15. Forbidden Practices

The system MUST NOT:

- produce non-normalized IR
- skip validation
- generate non-deterministic ordering
- include hidden runtime state
- mutate IR after hashing

---

## 16. Future Extensions (Non-Normative)

- timeline integration
- multi-agent IR
- probabilistic annotations
- extended audit metadata