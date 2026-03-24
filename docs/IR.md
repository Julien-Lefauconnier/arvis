# ARVIS Intermediate Representation (IR)

## Version

Current version: `arvis-ir.v1`

---

## Definition

The IR is the **canonical, versioned output** of ARVIS cognition.

It is:

- deterministic
- serializable
- model-independent
- forward-compatible

---

## Top-Level Structure

```json
{
  "version": "arvis-ir.v1",
  "fingerprint": "stable",
  "input": {...},
  "context": {...},
  "decision": {...},
  "state": {...},
  "gate": {...},
  "meta": {}
}
```

---

## Fields

### input

Currently not populated in v1.
Reserved for future versions.

### context

Currently not populated in v1.
Reserved for future versions.

### decision

Represents the final decision outcome.

Properties:

- action decision
- execution intent
- confirmation requirements

---

## state

Represents the scientific cognitive state.

Properties:

- stability signals
- risk
- drift
- regime

---

## gate

Represents the stability validation outcome.

Values:

- allow
- require_confirmation
- abstain

---

## meta

Reserved for extensions.

Must:

- never break existing fields
- be optional

---

## Invariants

The IR guarantees:

1. No hidden state
2. Pure transformation from pipeline output
3. Deterministic serialization
4. Backward compatibility across versions
5. Schema stability (field meaning cannot change without version bump)

---

## Compatibility Rules

### Minor updates

- new fields allowed
- existing fields unchanged

### Major updates

- version bump required
- breaking changes documented

---

## Use Cases

- LLM prompting
- system interoperability
- replay & simulation
- auditing

---

## Design Principle

The IR is the contract between cognition and the external world.