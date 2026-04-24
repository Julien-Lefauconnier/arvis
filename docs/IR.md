# ARVIS Intermediate Representation (IR)

## Version

Current version: `arvis-ir.v1`

The version identifies the public machine contract, not internal implementation details.

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
- long-term compatibility
- downstream automation

It is NOT constrained by external canonical signal registries.

IMPORTANT:

The IR represents **cognitive evaluation**, not the final user response.

- It contains validated intent, state, and decision signals
- It does NOT contain conversational realization or generated outputs

Response generation occurs in the Conversation & Realization layers.

The IR is where cognition becomes portable.

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

Implementation note:

- builder = semantic aggregation
- normalizer = canonical ordering
- validator = schema / consistency checks
- serializer = stable representation
- hasher = commitment layer
- envelope = transport wrapper

This ensures:

- deterministic structure
- order-invariant normalization
- validation before exposure
- stable hashing
- replayability

Construction precondition:

- pipeline execution must be finalized
- the terminal result must be non-null
- the cognitive context must be in a valid post-pipeline state

IR construction from partial or non-finalized execution is invalid.

No intermediate pipeline state may be treated as canonical IR.

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

Exact fields may evolve under compatibility rules while preserving semantics.

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

Purpose:
- provenance
- identity of originating request
- deterministic replay anchoring

### 2. Context (CognitiveContextIR)

Represents execution context.

Fields:

- user_id
- session_id
- conversation_mode
- long_memory_constraints
- long_memory_preferences
- extra

Purpose:
- bounded execution context
- memory-derived constraints
- non-cognitive metadata required for interpretation

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

Purpose:
- explain what cognition concluded
- expose why it concluded it
- preserve structured decision semantics

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

Purpose:
- expose normalized internal state
- support audits and diagnostics
- preserve control/stability context

### 5. Gate (CognitiveGateIR)

Represents the stability validation outcome.

Fields:

- verdict (ALLOW / REQUIRE_CONFIRMATION / ABSTAIN)
- bundle_id
- reason_codes

Purpose:
- expose admissibility result
- explain enforcement outcome
- prove that unsafe cognition was filtered

---

## Optional Extensions

For any fixed configuration, inclusion or exclusion of these sections MUST remain deterministic.

Optional does NOT mean arbitrary:
- identical finalized cognition + identical configuration → identical IR structure

Depending on deterministic system configuration, IR may include:

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

Optional sections must remain deterministic under the same finalized cognition and configuration.

---

## Normalization

The IR is normalized before validation:

- reason codes are sorted
- actions are ordered
- conflicts and gaps are canonicalized
- context hints are sorted

This guarantees:

  - identical semantic IR → identical normalized IR

Normalization removes accidental differences, not semantic differences.
---

## Validation

The IR is validated before serialization.

Validation enforces:

- schema integrity
- field consistency
- type correctness
- version compatibility
- absence of malformed values

---

## Serialization

The IR is serialized into a deterministic representation:

```python
serialized = to_canonical_dict(...)
```

Key ordering and canonical formatting must remain stable.

---

## Hashing

A stable hash is computed:

```python
hash_value = CognitiveIRHasher.hash(ir)
```

Guarantees:

- identical IR → identical hash
- normalization ensures hash stability
- supports timeline commitments and tamper evidence

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

Typical uses:

- storage
- transport
- external verification
- replay packages

---

## Invariants

The IR guarantees:

- Determinism
- No hidden state
- Construction ONLY from finalized cognitive execution
- No derivation from partial pipeline state
- Deterministic transformation from finalized cognitive context
- Stable normalization
- Stable hashing
- Replay consistency
- Information completeness (no semantic loss from finalized pipeline output)

For avoidance of doubt:

- intermediate stage outputs are not canonical IR inputs
- scheduler preemption does not change final IR semantics
- runtime orchestration order must not affect finalized IR content
- language realization changes must not alter IR content

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
- useful for regression testing

---

## Compatibility Rules

### Minor updates

- new fields allowed
- no change to existing semantics
- additive evolution only

### Major updates

- version bump required
- breaking changes documented
- migration path recommended

---

### Use Cases

- deterministic replay
- audit and compliance
- system interoperability
- LLM structured prompting
- trace verification
- debugging
- regression snapshots
- contract testing

NOTE:

For interoperability with **external signal-based systems** (e.g. Veramem Kernel),
the IR MUST be transformed through a dedicated projection layer:

→ Kernel Adapter (Canonical Projection Layer)

This transformation:

- is deterministic
- is rule-based
- is lossy (information may be reduced to match canonical constraints)
- does NOT belong to the IR itself

IR remains richer than any projected external signal form.

---

## Design Principle

The IR is the canonical machine contract of ARVIS.

It is the boundary between:

- finalized cognition
- downstream response construction
- external machine consumers

It is NOT:

- a conversational response
- a stage-level artifact
- a runtime scheduling artifact

It connects:

- the internal CognitiveState
- the pipeline execution
- external consumers

- replay systems
- audit systems
- interoperability layers

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
- replay-oriented

### Canonical Signals (External Systems)

- constrained
- registry-bound
- reduced representation
- interoperability-focused
- compliance / transport oriented

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

---

## One-Line Summary

**CognitiveState is internal truth. IR is portable truth. Canonical Signals are projected truth.**