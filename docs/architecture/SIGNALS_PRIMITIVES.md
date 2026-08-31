# Signals: Cognitive Kernel Abstraction

## Overview

Signals are the fundamental abstraction used to represent normalized cognitive quantities
inside the ARVIS kernel.

They replace raw scalar values (`float`) with semantically meaningful, typed objects.

## Design Principles

- **Normalized**: all signals are constrained to [0, 1]
- **Immutable**: signals are frozen dataclasses
- **ZKCS-safe**: no internal metadata is exposed
- **Composable**: signals can be combined and transformed
- **Semantic-first**: logic should depend on signal meaning, not raw thresholds

## Available Signals

### RiskSignal

Represents collapse risk.

```python
RiskSignal(0.0 → 1.0)
```

Helpers:

- is_low()
- is_moderate()
- is_high()

Note: these signal bands (0.3 / 0.7 / 0.85) are descriptive
observability vocabulary and deliberately distinct from the input-risk
gate's decision thresholds (0.4 / 0.8, `arvis/kernel/gate/input_risk.py`).
`is_high()` describes a signal; only the gate's constants decide.
- is_critical()
- is_transition_zone()
- is_unstable_zone()



### UncertaintySignal

Represents epistemic uncertainty.

```python
UncertaintySignal(0.0 → 1.0)
```

Helpers:

- is_high()

### DriftSignal

Represents system drift / instability.

```python
DriftSignal(0.0 → 1.0)
```

Helpers:

- is_high()

## Signal Boundary

Controllers should never depend directly on raw floats.

Instead, they should coerce at the boundary:

```python
from arvis.math.signals.coercion import to_float, to_risk
```

or use semantic helpers:

```python
if risk.is_critical():
```

## Migration Strategy

The system supports hybrid usage:

- float (legacy)
- Signal (preferred)

Controllers are progressively migrating toward full signal-native logic.

## Long-term Vision

Signals will become the primary carrier of:

- uncertainty
- risk
- stability
- trust

Future evolutions may include:

- probabilistic signals
- interval-based signals
- distribution-aware signals

## Role in Control Loop

Signals are not passive representations.

They are actively used to:

- drive control adaptation (epsilon, exploration)
- influence decision gating
- propagate stability constraints

They form a **closed-loop interface between measurement and control**.
