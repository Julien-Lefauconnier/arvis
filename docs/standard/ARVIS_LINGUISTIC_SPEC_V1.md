# LINGUISTIC LAYER SPEC (v1 — Normative)

## 1. Purpose

The Linguistic Layer defines how a structured response plan is transformed into a realized communicative output.

It operates strictly:

ResponsePlan → Linguistic Representation → Output

It ensures:

- controlled generation
- deterministic structure
- separation between cognition and language
- safe interaction with generative systems (LLMs or templates)

---

## 2. Architectural Position

```text
Cognitive Pipeline
→ Decision (validated)

→ Conversation Layer
→ ResponsePlan

→ Linguistic Layer (THIS)

→ Realization Layer (templates / LLM)
→ Output
```

IMPORTANT:

The Linguistic Layer operates strictly after IR and ResponsePlan.
It MUST treat ResponsePlan as a fully constrained, pre-validated input.

---

## 3. Core Principle

    The Linguistic Layer does NOT decide what to say.
    It determines how to express an already validated intent.
    It MUST NOT introduce new semantic content beyond the ResponsePlan.


---

## 4. Layer Decomposition

The Linguistic Layer is composed of four subsystems:

```text
1. Act System
2. Generation Frame System
3. Lexicon System
4. Realization System
```

---

## 5. Act System

### Definition

Defines the type of communicative act.

Located in:

```text
arvis/linguistic/acts/
```

---

### Core Object: LinguisticAct

Represents the final communicative intent.

Examples:

- INFORM
- ASK_CONFIRMATION
- REFUSE
- EXECUTE_ACTION

Constraints:

- MUST be derived strictly from ResponsePlan
- MUST be deterministic
- MUST NOT introduce new semantics

---

### Act Mapping

Defined in:

```text
gate_mapping.py
act_types.py
mode_act_policy.py
```

Maps:

```text
ResponseStrategyDecision → LinguisticAct
```

More precisely:

CognitiveIR → ResponseStrategyDecision → ResponsePlan → LinguisticAct

### Invariants

- MUST be deterministic
- MUST NOT introduce new reasoning
- MUST remain consistent with decision + strategy

---

## 6. Generation Frame System

### Definition

Defines the structured representation of the message before generation.

Located in:

```text
arvis/linguistic/generation/
```

---

### Core Object: GenerationFrame

Represents:

- semantic structure
- content blocks
- constraints
- tone and mode

Constraints:

- MUST be fully derived from ResponsePlan
- MUST NOT introduce new information

---

### Frame Builder

```text
frame_builder.py
```

Builds:

```text
ResponsePlan → GenerationFrame
```

Constraints:

- MUST be deterministic
- MUST preserve all ResponsePlan constraints exactly

---

### Responsibilities

- structure message
- enforce constraints
- prepare content for realization

---

### Invariants

- MUST be deterministic
- MUST NOT contain final text
- MUST encode all required structure

---

## 7. Lexicon System

### Definition

Provides controlled vocabulary and domain-specific language.

Located in:

```text
arvis/linguistic/lexicon/
```

---

### Components

- lexicon_registry.py
- lexicon_resolver.py
- domain lexicons (finance, legal, security, etc.)

---

### Role

- normalize terminology
- enforce domain constraints
- ensure semantic consistency

Constraints:

- MUST NOT introduce semantic transformations
- MUST be a pure normalization layer

---

### Invariants

- MUST be deterministic
- MUST be versioned
- MUST NOT introduce ambiguity

---

## 8. Realization System

### Definition

Transforms structured representation into final output.

Located in:

```text
arvis/linguistic/realization/
```

---

### Components

- realization_service.py
- default_templates.py
- prompt_builder.py
- llm_executor.py

---

### Realization Modes

Defined in:

```text
response_realization_mode.py
```

Supports:

- TEMPLATE (deterministic)
- LLM (controlled generation)

---

### Flow

```text
GenerationFrame → PromptBuilder → LLMExecutor
```

or

```text
GenerationFrame → Template → Output
```

---

### Invariants

- MUST NOT alter decision semantics
- MUST respect ResponsePlan constraints
- MUST remain bounded by GenerationFrame
- MUST be auditable
- MUST NOT introduce new intent

---

## 9. Prompt Builder (LLM Integration)

### Role

Constructs a controlled prompt:

```text
GenerationFrame → Prompt
```

Ensures:

- no prompt leakage
- constraint preservation
- deterministic structure

Constraints:

- MUST NOT introduce implicit instructions not present in GenerationFrame

---

### Invariants

- MUST NOT inject new intent
- MUST preserve all constraints
- MUST be deterministic given same inputs

---

## 10. Separation from Cognition

The Linguistic Layer MUST NOT:

- perform reasoning
- modify decisions
- introduce new information not present in ResponsePlan
- depend directly on CognitiveState or pipeline internals

---

## 11. Determinism Model

Determinism applies at two levels:

### Structural Determinism
- Act
- Frame
- Plan

→ MUST be strictly deterministic

---

### Realization Determinism

- TEMPLATE → deterministic
- LLM → bounded, but not strictly deterministic

IMPORTANT:

    Non-determinism is allowed ONLY in the realization phase.

Even in LLM mode:

- structure MUST remain deterministic
- constraints MUST be strictly enforced

---

## 12. Auditability

The system MUST allow reconstruction of:

```text
ResponsePlan
→ LinguisticAct
→ GenerationFrame
→ Output
```

Full traceability chain:

CognitiveIR → ResponsePlan → LinguisticAct → GenerationFrame → Output

---

## 13. Relation to Public Objects

Public objects include:

- LinguisticAct
- ResponsePlan
- ResponseStrategyDecision

These objects MUST comply with ARVIS_PUBLIC_OBJECT.md invariants.

The following are NOT public:

- GenerationFrame
- Prompt
- internal lexicon resolution

---

## 14. Security Model

The Linguistic Layer enforces:

- no uncontrolled generation
- no leakage of internal state
- strict constraint adherence
- no introduction of unauthorized content
- strict boundary enforcement with IR-derived data only

---

## 15. Invariants

- No decision override
- No hidden reasoning
- Deterministic structure
- Controlled realization
- Full traceability
- MUST NOT introduce new semantic content
- MUST operate strictly post-ResponsePlan