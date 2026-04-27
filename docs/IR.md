# ARVIS Intermediate Representation (IR)

## Executive Summary

The **Intermediate Representation (IR)** is the portable machine contract of ARVIS.

It transforms an internal governed decision into a deterministic, replayable, verifiable artifact.

Think of it as:

```text
Decision Intelligence → Portable Truth
```

The IR is how ARVIS outputs cognition without exposing internal implementation details.

---

## Why IR Exists

Most AI systems only return:

- text
- probabilities
- logs
- opaque outputs

That is insufficient for serious systems.

ARVIS introduces IR so decisions can be:

- replayed
- audited
- versioned
- verified
- transported
- integrated into other systems

---

## Core Principle

  If a decision matters, it must exist as a structured artifact.

---

## What IR Is

The ARVIS IR is:

- deterministic
- machine-readable
- replay-ready
- hashable
- stable across refactors
- independent from language generation

It represents:

- input context
- governed decision
- gate outcome
- reasoning metadata
- commitments
- optional observability state

---

## What IR Is Not

IR is not:

- chatbot output
- prompt text
- UI response
- random debug logs
- hidden internal memory dump

It is a governed contract.

---

## Conceptual Flow

```text
Input
 ↓
Cognitive Pipeline
 ↓
Decision Validation
 ↓
IR Construction
 ↓
Replay / Audit / Integration
```

---

## Example Usage

```python
from arvis import CognitiveOS

os = CognitiveOS()

ir = os.run_ir(
    user_id="demo",
    cognitive_input={"action": "approve_invoice", "risk": 0.22},
)

print(ir)
```

---

## Typical IR Shape

```json
{
  "version": "1.0.0",
  "fingerprint": "...",
  "input": {...},
  "context": {...},
  "decision": {...},
  "gate": {...},
  "state": {...},
  "global_commitment": "..."
}
```

Exact fields may evolve under compatibility rules.

---

## Major Components

### 1. Version Layer

Tracks contract version.

```json
{
  "version": "1.0.0"
}
```

Purpose:

- compatibility
- migrations
- contract governance

---

### 2. Input Section

Captures the governed originating request.

Examples:

- action request
- query
- transaction proposal
- tool invocation candidate

```json
{
  "input": {
    "action": "wire_transfer",
    "risk": 0.91
  }
}
```

---

### 3. Context Section

Bounded execution context.

May include:

- user id
- memory constraints
- session hints
- governance metadata

Not uncontrolled hidden state.

---

### 4. Decision Section

Represents what ARVIS concluded.

Examples:

- allow
- deny
- review
- confirm
- abstain

May include reason codes.

```json
{
  "decision": {
    "status": "REVIEW"
  }
}
```

---

### 5. Gate Section

Critical safety boundary.

Explains whether cognition passed admissibility checks.

Examples:

- stability insufficient
- risk too high
- uncertainty elevated
- human approval required

---

### 6. State Section

Optional structured runtime state.

May include:

- confidence
- regime
- control indicators
- stability snapshots

Useful for diagnostics and regulated environments.

---

### 7. Commitment Layer

Cryptographic-style deterministic fingerprint.

```json
{
  "global_commitment": "8642d95cfdb73c16..."
}
```

Purpose:

- tamper evidence
- equality checks
- replay verification

---

## Determinism

One of the strongest ARVIS properties.

Same governed input + same context:

```text
same IR
same commitment
same replay result
```

example :

```python
r1 = os.run("u1", payload)
r2 = os.replay(r1.to_ir())
```

---

## Replay

IR enables deterministic replay.

Use cases:

- incidents
- compliance review
- dispute resolution
- regression testing
- simulation

```python
result = os.replay(ir)
```

---

## Why This Matters

Without IR:

```text
AI said something.
No one knows why.
```

With IR:

```text
Decision made.
Reason governed.
Commitment recorded.
Replay possible.
```

---

## IR vs Logs

### Logs

- noisy
- inconsistent
- environment-dependent

### IR

- canonical
- stable
- machine-consumable
- deterministic

IR is stronger than logs.

---

## IR vs API Response Text

### Response Text

Human-facing explanation.

### IR

Machine-facing truth artifact.

These should remain separate.

---

## IR vs LLM Outputs

LLM outputs are language artifacts.

IR is a governance artifact.

ARVIS can use language models, but IR remains independent of them.

---

## Enterprise Use Cases

### Finance

- trade approvals
- replayable risk screening
- audit evidence

### Healthcare

- triage governance trails
- approval checkpoints

### Internal Automation

- invoice approvals
- HR workflows
- CRM updates

### Agent Systems

- portable state handoff
- governed tool actions

---

## Example

### Request

```json
{
  "action": "delete_customer_account",
  "risk": 0.55
}
```

### IR Outcome

```text
Decision: REVIEW
Approval Required: YES
Commitment: stable
Replay Ready: YES
```

---

## Compatibility Rules

### Minor Versions

Allowed:

- additive fields
- richer metadata
- optional sections

### Major Versions

Required when:

- semantics change
- breaking structure changes
- replay assumptions change

---

## Design Philosophy

ARVIS treats decisions like financial transactions:

They should leave structured records.

---

## Mental Model

Think of IR as:

```text
PDF for documents
Git commit for code
IR for governed cognition
```

---

## One-Line Summary

  Internal reasoning becomes trusted portable truth through IR.