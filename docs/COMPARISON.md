# Where ARVIS sits among the guardrail tools

Integrators evaluating ARVIS usually arrive from one of three tool
families: content guardrails (NVIDIA NeMo Guardrails), output
validators (Guardrails AI), or orchestrator middleware (LangChain
and LangGraph hooks, interrupts and checkpointers). The honest
answer to "which one should I use" is usually "one of those AND
this": they do a job ARVIS deliberately does not do, and ARVIS does
a job none of them claims.

Written 2026-09-03 against the projects' public documentation; these
tools evolve. If a capability is misstated here, open a
`guarantee_mismatch` issue and it will be corrected: a comparison
only helps while it is true.

## The two different jobs

A content layer decides what a model may SAY: moderation, topical
rails, jailbreak screening, schema and quality validation of the
output text.

A governance layer decides what the system may DO, and proves it
afterwards: graded authorization of acts, a bound human-confirmation
state, an effect boundary nothing bypasses, and a record an auditor
can replay.

ARVIS is the second thing only. Nothing in it inspects the content
of a completion, and running it does not reduce the need for a
content layer where one is warranted.

## Capability by capability

"yes" means the project documents and ships it as a core capability;
"partial" means it exists with material limits stated inline; "no"
means it is not the project's job (which is not a criticism).

| Capability | NeMo Guardrails | Guardrails AI | LangGraph middleware | ARVIS |
| --- | --- | --- | --- | --- |
| Content moderation, topical rails | yes (Colang flows, moderation models) | partial (validators) | no (bring your own) | no |
| Output schema and quality validation | partial | yes (validator hub, structured output) | no | no (tool INPUT schemas only, F-020) |
| Graded action authorization (allow / confirm / block) | no | no | partial (interrupts you wire yourself) | yes (the verdict bands, monotone by F-001) |
| Human confirmation as a bound, versioned state | no | no | partial (human-in-the-loop interrupts) | yes (confirmation format versioned, example 04) |
| Mediated effect boundary (no act outside it) | no | no | no (discipline, not mechanism) | yes (cognitive syscalls, sealed context, single-use capabilities) |
| Hashed, composed audit commitments | no | no | no | yes (F-007; registry, config, policies, journals) |
| Deterministic bit-identical replay of a decision | no | no | partial (checkpoint resume, not committed re-verification) | yes (authenticated replay against an external anchor, example 02) |
| Decision-loop stability monitoring | no | no | no | yes, with stated limits (measured contraction, certified risk ceiling; see the caveats below) |
| EU AI Act capability mapping, test-pinned | no | no | no | yes ([compliance/EU_AI_ACT_CAPABILITY_MAPPING.md](compliance/EU_AI_ACT_CAPABILITY_MAPPING.md)) |

## What the others do that ARVIS does not

NeMo Guardrails gives you conversational flow control in Colang,
moderation models and topical rails with low added latency; if your
risk is what the model says to users, start there. Guardrails AI
gives you composable output validation against schemas and quality
checks with a large validator hub; if your risk is malformed or
low-quality output entering downstream systems, start there.
LangGraph gives you the orchestration fabric itself, with
checkpointing and human-in-the-loop interrupts; ARVIS assumes you
have such a host and governs its acts rather than replacing it.

## ARVIS's own caveats, in one place

The 0.1 series governs structured inputs best: the graded bands ride
the explicit-risk contract, a bare text prompt lands conservatively
in REQUIRES_CONFIRMATION, and the stability guarantees have teeth
only when the host threads the scientific state and feeds structured
signals ([PATH_TO_ALLOW.md](PATH_TO_ALLOW.md) is the honest map).
The bundled LLM adapters are experimental and the recommended
pattern does not need them ([FIRST_REAL_CALL.md](FIRST_REAL_CALL.md)
calls your provider SDK directly). The validation corpus is
synthetic and the mathematics have not yet had external review; the
README's "What ARVIS Does Not Claim" section is the authoritative
list.

## Running them together

The composition is natural and loses nothing: the content layer
screens the model's text; the host maps surviving proposals onto its
own risk policy; ARVIS authorizes, holds or blocks the act, binds
any human confirmation, and commits the whole decision to a
replayable record. Fifteen minutes of that pattern is
[FIRST_REAL_CALL.md](FIRST_REAL_CALL.md); the vocabulary bridge is
[GLOSSARY.md](GLOSSARY.md).

Project references: [NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails),
[Guardrails AI](https://www.guardrailsai.com/),
[LangGraph](https://langchain-ai.github.io/langgraph/).
