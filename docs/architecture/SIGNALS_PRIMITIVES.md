# Signals — Cognitive Kernel Abstraction

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

Instead, they should:
```python
from arvis.math.signals.utils import signal_value
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