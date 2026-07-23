# ARVIS documentation

Fifty-six documents, four kinds. This page says which kind answers which
question, so you land in the right one rather than reading three.

- **Standard** (`standard/`) states what a conforming implementation MUST do.
  Normative.
- **Architecture** (`architecture/`, and the top-level overviews) describes how
  this implementation is built. Descriptive.
- **Math** (`math/`) proves what holds, and states where the proofs stop.
- **Tools** (`tools/`) is the practical guide for anyone writing a tool.

If a document contradicts the code, that is a defect worth reporting, not a
detail. See [CONTRIBUTING.md](../CONTRIBUTING.md).

## Start here

| You want to | Read |
| --- | --- |
| understand what ARVIS is for | [WHY_ARVIS.md](WHY_ARVIS.md), [OVERVIEW.md](OVERVIEW.md) |
| see how it differs from calling a model | [ARVIS_VS_LLM.md](ARVIS_VS_LLM.md) |
| know what is promised, and how far | [../VERSIONING.md](../VERSIONING.md) |
| write a tool | [tools/TOOL_AUTHORING_GUIDE.md](tools/TOOL_AUTHORING_GUIDE.md) |
| contribute | [../CONTRIBUTING.md](../CONTRIBUTING.md) |

## The standard

[ARVIS_SPEC_HIERARCHY.md](standard/ARVIS_SPEC_HIERARCHY.md) orders the
specifications and is the right entry point. The individual specs cover the
kernel core and its services, syscalls, access, decision and gate, the IR,
projection and the validity envelope, memory, conversation, the VFS, the
linguistic layer, the reason-code registry, the public object, and the
compliance suite.

## Architecture

| Document | Answers |
| --- | --- |
| [ARCHITECTURE.md](ARCHITECTURE.md) | how the pieces fit together |
| [ARCHITECTURE_INVARIANTS.md](ARCHITECTURE_INVARIANTS.md) | what must remain true |
| [PIPELINE.md](PIPELINE.md) | what happens during one turn |
| [architecture/EFFECT_PATH.md](architecture/EFFECT_PATH.md) | how an external effect is authorized and sealed |
| [architecture/RUNTIME_LIFECYCLE.md](architecture/RUNTIME_LIFECYCLE.md) | what the runtime does over time |
| [architecture/KERNEL_ADAPTERS.md](architecture/KERNEL_ADAPTERS.md) | how signals reach the kernel |
| [architecture/SIGNALS_PRIMITIVES.md](architecture/SIGNALS_PRIMITIVES.md) | the signal vocabulary |
| [COGNITIVE_STATE.md](COGNITIVE_STATE.md) | what the runtime holds between turns |
| [IR.md](IR.md) | what the intermediate representation carries |
| [REFLEXIVE.md](REFLEXIVE.md) | how the runtime describes itself |
| [VERSIONS.md](VERSIONS.md) | which version constant governs what |

Read `EFFECT_PATH.md` before changing anything under `kernel_core/syscalls/` or
`tools/`. Its invariants are pinned by `tests/adversarial/`, and a change that
relaxes one is not a refactor.

## Math

`math/` runs from M0 to M15. M0 sets the system boundary, M1 the assumptions,
M2 the proof skeleton; M3 covers the cognitive state, observation and the
validated projection domain; the later documents cover stability, the
projection control operator and the decision lattice.

Two are worth reading even if you skip the proofs:

- [M13](math/M13_formal_limits_assumptions_boundaries_open_problems.md), which
  states the limits, the boundaries and the open problems;
- [M1c](math/M1c_result_inventory.md), the inventory of what is actually
  proven.

The results hold **on the documented projected domain**, not on arbitrary
inputs. `VERSIONING.md` states which certificate axes are measured at runtime
and which are not, and the two must be read together: a proof about a domain
says nothing about an axis the runtime never evaluates.

## Tools

[TOOL_SYSTEM_V1.md](tools/TOOL_SYSTEM_V1.md) for the model,
[TOOL_LIFECYCLE.md](tools/TOOL_LIFECYCLE.md) for what happens to a call, and
[TOOL_AUTHORING_GUIDE.md](tools/TOOL_AUTHORING_GUIDE.md) to write one.
