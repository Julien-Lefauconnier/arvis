# ARVIS

**A runtime assurance kernel for LLM-based systems.**

[![CI](https://github.com/Julien-Lefauconnier/arvis/actions/workflows/CI.yml/badge.svg)](https://github.com/Julien-Lefauconnier/arvis/actions/workflows/CI.yml)
[![PyPI](https://img.shields.io/pypi/v/arvis)](https://pypi.org/project/arvis/)
[![Python](https://img.shields.io/pypi/pyversions/arvis)](https://pypi.org/project/arvis/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](https://github.com/Julien-Lefauconnier/arvis/blob/main/LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22280253.svg)](https://doi.org/10.5281/zenodo.22280253)

Your application asks ARVIS, on every turn, whether a proposed **act** may
happen. ARVIS returns a graded verdict (allow, require human confirmation,
block), refuses to relax it downstream, fails closed wherever its own state
is unknown, and leaves a record from which the decision replays bit for bit.

> Documentation site: <https://julien-lefauconnier.github.io/arvis/>
> (full docs, generated API reference, search).
> Status `0.1.0b8.dev0`, beta series. Python 3.11+.

## What it does not do

Read this before the rest. Two lines of code make the first point better
than a paragraph:

```python
from arvis import ArvisEngine

for prompt in ("What is 2+2?", "Delete all production databases now"):
    print(prompt, "->", ArvisEngine().ask(prompt).status)
```

```text
What is 2+2? -> REQUIRES_CONFIRMATION
Delete all production databases now -> REQUIRES_CONFIRMATION
```

1. **ARVIS does not read your content.** The two prompts above are governed
   identically, because the verdict comes from declared risk, payload
   structure and measured trajectory state, never from what the text says.
   If you want a model to judge whether a sentence is acceptable, you want a
   content filter, and
   [COMPARISON.md](https://github.com/Julien-Lefauconnier/arvis/blob/main/docs/COMPARISON.md)
   names the ones to use. ARVIS governs whether an act may happen and proves
   what governed it. Different job.
2. **The `production` profile refuses everything** the partial projection
   cannot certify in this beta, including a pure `{"risk": 0.0}` payload.
   That is deliberate fail-closed behaviour, and it means the graded flow
   below belongs to the default profile only.
3. **`ALLOW` is conditional by construction.** In the default profile it is
   immediate on a pure declared-risk payload (below); in the empirical
   campaigns, on adversarial corpora, it is deliberately rare.

It promises nothing about correctness outside its documented assumptions,
arbitrary LLM behaviour, or the quality of a model's answer.

> The long-term ambition is a cognitive operating system. What ships today
> is the kernel. That distinction, and where the rest is going, is in
> [the author's note](https://github.com/Julien-Lefauconnier/arvis/blob/main/docs/AUTHORS_NOTE.md).

## Install

```bash
pip install arvis
```

From source, for development:

```bash
git clone https://github.com/Julien-Lefauconnier/arvis
cd arvis
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
bash scripts/run_quality_gate.sh
```

`scripts/run_quality_gate.sh` is the canonical gate: the same pinned tools
and the same security threshold CI runs, parity enforced by test.

## Quick start

The graded path, on the default profile:

```python
from arvis import ArvisEngine

for risk in (0.05, 0.5, 0.95):
    print(risk, "->", ArvisEngine().ask({"risk": risk}).status)
```

```text
0.05 -> ALLOWED
0.5 -> REQUIRES_CONFIRMATION
0.95 -> BLOCKED
```

Thresholds, from `arvis/kernel/gate/input_risk.py`: `risk < 0.4` is ALLOWED,
`0.4 <= risk < 0.8` requires confirmation, `risk >= 0.8` is BLOCKED. `NaN`
and infinities fail closed to BLOCKED.

Grading applies only to a payload whose single key is `risk`. A mixed
payload carries content, and a declared risk may only harden the verdict of
content, never relax it, so `{"risk": 0.3, "action": ...}` is governed by
the projection verdict (BLOCKED for unprojected content in this beta).

Every decision explains itself and commits to what governed it:

```python
from arvis import CognitiveOS

result = CognitiveOS().run(user_id="demo", cognitive_input={"risk": 0.92})

print(result.explain())
```

```text
Status         : BLOCKED
Approval Need  : NO
Reason         : execution_blocked
Commitment     : 48d6097aae8efd8c...
Trace          : Available
```

The commitment is deterministic within a version: it binds the governance
identity (tool registry, effective configuration, policy tables, redacted
effect journals), so the same input on your checkout gives a stable hash
whose value differs from the illustrative one above whenever a format
version moved between releases. `result.to_ir()` exports the run, and
`examples/02_deterministic_replay.py` replays it bit for bit against an
externally stored anchor.

`summary()` gives the one-line form. The measured axes and the declared
scalar stay distinct: `Stability`, `Risk`, `RiskCeiling` and `Regime` are
what the contraction monitor measured about this run, while `DeclaredRisk`
is the untrusted value the caller asserted, and only the declared-risk gate
acts on it. On a first turn, nothing bad has been observed (`Risk=0.00`) and
nothing has been ruled out either (`RiskCeiling=1.00 (CRITICAL)`); the
ceiling tightens as the trajectory accumulates evidence, which requires the
host to thread `scientific_state` between turns.

**Next:** [fifteen minutes to a governed model call](https://github.com/Julien-Lefauconnier/arvis/blob/main/docs/FIRST_REAL_CALL.md),
then [getting started end to end](https://github.com/Julien-Lefauconnier/arvis/blob/main/docs/GETTING_STARTED.md).
Unfamiliar vocabulary is mapped to standard concepts in
[GLOSSARY.md](https://github.com/Julien-Lefauconnier/arvis/blob/main/docs/GLOSSARY.md).

## Runtime profiles

The two named profiles differ in kind, not in degree:

| Posture | `local` (default) | `production` |
|---|---|---|
| Input-risk gate | graded, three bands | harden-only: every declared risk refused |
| Tool gates | permissive default | deny-by-default |
| Tool registry | open | frozen |
| Host runtime controls | accepted | rejected |
| Global stability action | monitor | confirm |
| Switching envelope | monitor | enforce |

The default is a development posture for embedding and iteration.
`CognitiveOSConfig.production()` is the deployment posture, and in this beta
it refuses every input the partial projection cannot certify.

## The two public surfaces

| Surface | Intended use |
|---|---|
| `arvis` (root, 11 symbols) | Applications: `ArvisEngine` for most integrations, `CognitiveOS` for replay, IR control and pipeline customization |
| `arvis.host_api` (pinned modules) | Hosts: tools, access and identity, memory, VFS, services, telemetry, each import path pinned by contract test |

Anything else (`arvis.api`, deep module paths) is internal and may change in
any release. Production effects run through `engine.run_as(principal, ...)`
with an `AuthenticatedPrincipal` from `arvis.host_api.access`; the deprecation
policy for both surfaces is in
[VERSIONING.md](https://github.com/Julien-Lefauconnier/arvis/blob/main/VERSIONING.md).

One engine executes one governed run at a time and is not thread-safe. The
documented lifecycle is one instance per turn
([RUNTIME_LIFECYCLE.md](https://github.com/Julien-Lefauconnier/arvis/blob/main/docs/architecture/RUNTIME_LIFECYCLE.md));
parallelism belongs to the host, by instantiation.

## Where ARVIS fits

ARVIS sits between an application's AI-generated proposals and its governed
tools. The host keeps identity, business rules, memory, models, storage and
external providers. Every real-world effect crosses one mediated boundary
with a sealed identity context, and each authorized tool receives a frozen
payload plus a single-use capability, never the mutable pipeline context.

* [Reference architecture](https://github.com/Julien-Lefauconnier/arvis/blob/main/docs/architecture/REFERENCE_ASSISTANT_ARCHITECTURE.md)
  and its [runnable example](https://github.com/Julien-Lefauconnier/arvis/blob/main/examples/11_governed_assistant.py)
* [The governed effect path](https://github.com/Julien-Lefauconnier/arvis/blob/main/docs/architecture/EFFECT_PATH.md)
  and the [tool authoring guide](https://github.com/Julien-Lefauconnier/arvis/blob/main/docs/tools/TOOL_AUTHORING_GUIDE.md)
* [VeraMem integration pattern](https://github.com/Julien-Lefauconnier/arvis/blob/main/docs/integration/VERAMEM_INTEGRATION_PATTERN.md)
  (the author's own application of the pattern, not an independent adoption,
  and not a dependency)

A governed turn costs about 6.4 ms median, engine construction 0.15 ms, with
the measurement script published
([PERFORMANCE.md](https://github.com/Julien-Lefauconnier/arvis/blob/main/docs/PERFORMANCE.md)).

## Validation

2900+ tests run in under 30 seconds: property-based, adversarial regressions
pinned on reproduced attack vectors, gate safety-ordering and
starvation-freedom properties, multi-instance isolation, and about forty
contract ratchets that can only tighten (import closure, docstring coverage,
doc claims, coverage floors, a decreasing ceiling on broad exception
handlers).

Beyond the suite, the mathematical claims are validated by pre-registered
campaigns: six M10 campaigns on two published synthetic corpora (1440 and
1632 turns), thresholds registered by commit before each run, judged 11 of
12 and 12 of 12, with the one failed criterion reported as failed rather
than adjusted. Artifacts are tracked and regenerate byte-identically, and a
ratchet keeps the report's headline numbers equal to the artifacts.

What the campaigns do not establish: the corpora are synthetic, small, and
produced by the author; alpha and L_T are measured report-only, so the
runtime constants remain declared assumptions; the switching axis is
monitor-only in the default posture; and no claim is made about the CONTENT
a model produces. The full report, including which criteria can fail, is
[the M10 report](https://github.com/Julien-Lefauconnier/arvis/blob/main/docs/math/M10_empirical_stability_validation_and_runtime_validation.md)
(read section 16 first); the integrator-facing account of what stands
between a call and an `ALLOW` is
[PATH_TO_ALLOW.md](https://github.com/Julien-Lefauconnier/arvis/blob/main/docs/PATH_TO_ALLOW.md).

## Citing ARVIS

> Lefauconnier, J. (2026). *ARVIS: A Runtime Assurance Kernel for LLM-Based
> Systems with Deterministic Replay and Pre-Registered Empirical
> Validation.* Zenodo.
> [10.5281/zenodo.22280253](https://doi.org/10.5281/zenodo.22280253)

The preprint describes software version `0.1.0b7` and has **not** been peer
reviewed: it is a citable statement of what this repository does and does
not establish, not an external validation of it.
[CITATION.cff](https://github.com/Julien-Lefauconnier/arvis/blob/main/CITATION.cff)
carries the same record machine-readably.

## Examples

Fifteen runnable examples, from `python examples/00_quickstart_engine.py` to
governing a real model call. The ones worth opening first: `01` gate
refusal, `02` deterministic replay, `05` tool governance, `13` the
end-to-end governed memory assistant, `14` a real model call with a host
risk policy. Full list in `examples/README.md`.

## Known limitations (0.1.0 beta)

**Stable, documented, tested:** the governed decision pipeline and
admissibility gate; the graded risk gate above; deterministic replayable IR
and timeline commitment; the syscall boundary for external effects including
a governed `llm.generate` path; tool authorization with a per-spec risk
budget; sealed effect contexts and receipt-activated single-use
capabilities; a typed runtime error model.

**Behavioural caveats, know these before deploying:**

* The `production` profile refuses everything, as stated above.
* The contraction monitor is the default core model: every run measures a
  Lyapunov state, its energy V, a drift score, a PAC risk ceiling and an
  empirical regime. **Trajectory properties need threaded state**: the engine
  is one-turn by design, so delta-V and the Lyapunov gate's trajectory branch
  only become live when the host threads the replayable `scientific_state`
  between turns (`run(..., extra={"scientific_state": previous})`, read back
  from `view.next_scientific_state`). A first, unthreaded turn is
  conservative by construction.
* Stability axes are reported only when measured: `summary()` returns
  `n/a`/`null` for axes a run did not compute, never zeros.

**Experimental, present but not part of the stable API:** long-term memory;
conversation state types; the natural-language input surface (a bare prompt
gets a minimal projection, hence REQUIRES_CONFIRMATION, not a full cognitive
projection); real LLM providers (the adapter path is wired end to end, the
bundled provider is a deterministic stub).

**Out of scope for 0.1:** the full projection Pi; risk gating beyond an
explicit top-level `risk` scalar; general formal guarantees over arbitrary
LLM behaviour; distributed registry, confirmation and idempotency
coordination. Formal guarantees apply only to the documented projected
domains and their assumptions.

## Versioning

| Axis | Value | Meaning |
|---|---|---|
| Package version | `0.1.0b8.dev0` | the distributed artifact (PEP 440) |
| API version | `0.1` | stable within the beta series under `VERSIONING.md` |
| Standard version | `draft-v1` | the ARVIS decision / IR specification |

## Project reference

- [CHANGELOG](https://github.com/Julien-Lefauconnier/arvis/blob/main/CHANGELOG.md): every campaign, every security fix, every deprecation.
- [SECURITY](https://github.com/Julien-Lefauconnier/arvis/blob/main/SECURITY.md): reporting, supported versions, audit-suppression policy.
- [CONTRIBUTING](https://github.com/Julien-Lefauconnier/arvis/blob/main/CONTRIBUTING.md): the quality gate is the contract; English everywhere.
- [Configuration](https://github.com/Julien-Lefauconnier/arvis/blob/main/docs/CONFIGURATION.md): every environment variable ARVIS reads.
- [Format versions](https://github.com/Julien-Lefauconnier/arvis/blob/main/docs/VERSIONS.md): the map of the version constants.
- [EU AI Act capability mapping](https://github.com/Julien-Lefauconnier/arvis/blob/main/docs/compliance/EU_AI_ACT_CAPABILITY_MAPPING.md): what the kernel contributes, article by article, and what stays with the host.

Licensed under [Apache-2.0](https://github.com/Julien-Lefauconnier/arvis/blob/main/LICENSE).
