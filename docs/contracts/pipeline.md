# Cognitive Pipeline Contract

## Overview

The cognitive pipeline is the core execution engine of the ARVIS system.

It transforms raw cognitive input into structured decisions through multiple layers.

## Contract Guarantees

After pipeline execution:

### Typed Outputs

The following fields MUST be present and typed:

- `collapse_risk` → `RiskSignal`
- `uncertainty` → `UncertaintySignal`
- `drift_score` → `DriftSignal`

### Stability

- No field should leak raw internal state
- All outputs must be normalized and safe

### Determinism

Given the same inputs and state:

- The pipeline must produce consistent outputs

---

## Compatibility

The pipeline supports both:

- float inputs
- signal inputs

However:

> signals are the canonical representation

---

## Testing

The contract is enforced by:

```python
tests/kernel/test_pipeline_contract.py
```

---

## Extension Rules

Any new pipeline output must:

1. Be typed
2. Be normalized
3. Be documented
4. Be tested

---

## Breaking Changes

Any change to:

- signal types
- pipeline outputs
- public API

must be considered a breaking change.