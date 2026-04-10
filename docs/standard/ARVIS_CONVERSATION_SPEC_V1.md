# CONVERSATION LAYER SPEC V1

## 1. Purpose

The Conversation Layer defines how a validated cognitive decision is transformed into a communicable structured response.

It operates strictly:

```text
AFTER cognition
AFTER decision validation
BEFORE linguistic realization
```

It ensures:

- safe communication
-  context-aware response shaping
- memory integration
- stability-aware interaction

---

## 2. Architectural Position

```text
Cognitive Pipeline
→ CognitiveState
→ Decision (Gate + Confirmation + Execution)
→ IR (canonical representation)

→ Conversation Layer (THIS)

→ Linguistic Layer
→ Realization Layer
→ Output
```

IMPORTANT:

The Conversation Layer operates strictly AFTER IR.
It MUST treat the IR as the single source of truth.

---

## 3. Core Principle

    The Conversation Layer does NOT perform cognition.
    It transforms a validated cognitive intent into a communicable response strategy and plan.

    It MUST NOT introduce new semantic information not present in the IR.

---

## 4. Core Objects

The following objects are defined as PUBLIC OBJECTS in ARVIS_PUBLIC_OBJECT.md:

- ResponseStrategyDecision
- ResponsePlan

### 4.1 ResponseStrategyDecision

Defined in:

```text
arvis/conversation/response_strategy_decision.py
```

Represents:

- the type of response behavior

Examples:

- ABSTENTION
- CONFIRMATION
- INFORMATIONAL
- ACTION

Invariants:

- MUST be derived strictly from CognitiveIR
- MUST NOT modify decision semantics
- MUST be deterministic
- MUST NOT depend on linguistic realization
- MUST NOT depend on runtime execution

---

### 4.2 ResponseStrategyType

Defined in:

```text
response_strategy_type.py
```

Defines the canonical strategy space.

---

### 4.3 ResponsePlan

Defined in:

```text
response_plan.py
response_plan_builder.py
```

Represents a structured plan for communication.

Contains:

- act type
- structure
- constraints
- realization hints

IMPORTANT:

    The ResponsePlan is NOT language
    It is a pre-linguistic communicative structure

Invariants:

- MUST be deterministic
- MUST be derived from CognitiveIR + ResponseStrategyDecision
- MUST NOT introduce new information
- MUST NOT contain natural language

---

### 4.4 ConversationContext

Defined in:

```text
conversation_context.py
```

Represents:

- conversational state
- user interaction mode
- contextual signals

Constraints:

- MUST be deterministic
- MUST NOT contain runtime-only execution state
- MUST remain consistent with CognitiveContextIR

---

### 4.5 ConversationOrchestrator

Defined in:

```text
conversation_orchestrator.py
```

Role:

```text
Decision + Context + Memory → ResponseStrategy → ResponsePlan
```

Constraints:

- MUST be deterministic
- MUST NOT introduce decision logic
- MUST operate strictly post-IR

---

## 5. Processing Flow

### Step 1 — Strategy Selection

```text
Decision → ResponseStrategyDecision
```

More precisely:

CognitiveIR → ResponseStrategyDecision

Inputs:

- Gate verdict
- confirmation state
- execution feasibility
- cognitive signals

---

### Step 2 — Context Integration

```text
ConversationContext + Memory → enriched context
```

Constraints:

- Memory MUST be applied through policy gates
- Memory MUST NOT introduce new decision semantics

Includes:

- user preferences
- conversation mode
- memory constraints

---

### Step 3 — Plan Construction

```text
ResponseStrategy → ResponsePlan
```

Plan defines:

- communicative intent
- structure
- constraints

---

### Step 4 — Stability Adaptation

Conversation may be adapted based on:

- stability signals
- uncertainty
- conflict pressure

These adaptations MUST:

- NOT modify decision semantics
- ONLY affect communication strategy or structure

---

## 6. Strategy Semantics

| Strategy      | Meaning                        |
| ------------- | ------------------------------ |
| ABSTENTION    | No response or refusal         |
| CONFIRMATION  | Ask for validation             |
| INFORMATIONAL | Provide structured information |
| ACTION        | Execute or suggest action      |

---

## 7. Memory Integration

The Conversation Layer integrates memory through:

```text
conversation_memory_bridge.py
conversation_memory_policy.py
```

Responsibilities:

- inject constraints into response
- adapt tone and structure
- restrict unsafe outputs

IMPORTANT:

    Memory does NOT alter cognition
    It constrains communication

- Memory usage MUST be deterministic
- Memory usage MUST be auditable via MemoryLongSnapshot

---

## 8. Adaptive Control

Conversation is dynamically regulated by:

- conversation_adaptive_controller.py
- conversation_stability_controller.py

This ensures:

- no conversational instability
- coherence preservation
- safe trajectory

Adaptive control MUST NOT:

- influence decision semantics
- override IR outputs

---

9. Separation of Concerns

The Conversation Layer MUST NOT:

- modify decision semantics
- override Gate verdict
- perform reasoning

It ONLY:

- interprets IR into communication

---

## 10. Output Contract

The output of the Conversation Layer is:

```python
ResponsePlan
```

This object is:

- deterministic (given same inputs)
- structured
- language-agnostic

It MUST be sufficient for deterministic linguistic realization.

---

## 11. Determinism Guarantees

Given identical inputs:

- same strategy MUST be selected
- same plan MUST be produced

---

## 12. Relation to IR

IMPORTANT:

- The Conversation Layer is NOT part of IR
- IR represents cognition
- Conversation represents communication

- The Conversation Layer MUST be a pure function of IR (+ context/memory)
- IR is the ONLY source of decision truth

---

## 13. Invariants

- No cognition performed
- No decision override
- Deterministic mapping
- Memory only constrains, never decides
- MUST NOT introduce new semantic content
- MUST operate strictly post-IR