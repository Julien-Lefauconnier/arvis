# EU AI Act capability mapping

This page maps obligations of the EU AI Act (Regulation (EU) 2024/1689)
onto the mechanisms ARVIS actually provides, so that the provider or
deployer of a host system integrating ARVIS can see, article by
article, what the kernel contributes to a compliance case and what
remains theirs. Every claimed mechanism is anchored to the invariant
and decision identifiers that resolve under
[docs/decisions/](../decisions/README.md) and to the code or example
that exercises it; a gate test (`tests/docs/test_ai_act_mapping.py`)
keeps the anchors resolvable and the status vocabulary closed.

This page is a capability mapping, not legal advice, and not a
conformity assessment. Integrating ARVIS does not make any system
compliant: compliance attaches to the AI system placed on the market
and to its provider's and deployers' processes. Engage qualified
counsel and, where required, a notified body.

Legal state this page was written against (2026-09-03): the AI Act as
amended by the Digital Omnibus (Regulation (EU) 2026/1744, in force
27 July 2026). Obligations for Annex III high-risk systems apply from
2 December 2027 and for Annex I embedded high-risk systems from
2 August 2028; prohibited practices, general-purpose model
obligations and the Article 50 transparency duties already apply.
Verify the current state before relying on any date here.

## Where ARVIS sits in the Act's cast

ARVIS is a software component, a runtime assurance kernel. It is not
an AI system in the Act's sense: it has no intended purpose without a
host, produces no content, and takes no decision about the world on
its own. The Act's obligations attach to providers and deployers of
AI systems and to providers of general-purpose AI models; none of
those roles is ARVIS's.

The Act names ARVIS's actual position. Article 25(4) obliges the
provider of a high-risk AI system and any third party supplying
tools, services, components or processes integrated into it to
specify, by written agreement, the information, capabilities and
technical access the provider needs, and then exempts third parties
that make such components publicly accessible under a free and
open-source licence. ARVIS is such a component, under Apache-2.0.
The exemption removes the mandated agreement, not the provider's
need: this page and the documents it links are that information,
provided in the open. The public surfaces are pinned
([VERSIONING.md](../../VERSIONING.md)), every stored format is
versioned ([VERSIONS.md](../VERSIONS.md)), and every governance
decision cited in the code resolves in
[docs/decisions/](../decisions/README.md).

## Status vocabulary

Four statuses, closed by the gate test:

- **Provided**: ARVIS supplies the runtime mechanism itself. The
  host still integrates, operates and retains.
- **Partial**: ARVIS mechanisms contribute materially, and material
  parts of the obligation remain outside the kernel.
- **Host obligation**: the obligation belongs to the host's provider
  or deployer; ARVIS supplies artifacts that make it dischargeable.
- **Out of scope**: nothing in ARVIS addresses it.

Partial coverage is not partial compliance. An obligation is met or
it is not; this page says which mechanisms exist, never that a duty
is discharged.

## Coverage summary

| Article | Obligation | Status |
| --- | --- | --- |
| Article 9 | Risk management system | Partial |
| Article 12 | Record-keeping | Provided |
| Article 13 | Transparency and provision of information to deployers | Partial |
| Article 14 | Human oversight | Partial |
| Article 15 | Accuracy, robustness and cybersecurity | Partial |
| Article 26 | Obligations of deployers | Host obligation |

## Article 9: risk management system

**Status: Partial.**

The obligation: a continuous, iterative risk management system over
the whole lifecycle, which identifies, estimates and evaluates risks
and adopts mitigation measures.

What ARVIS provides is the runtime instrument such a system can
build on. Risk is measured and certified per turn, not assumed: the
stability view carries the certified PAC risk ceiling beside the
empirical rate (`risk_ucb`, `risk_verdict`, DM-I3), and the verdict
floors are monotone and fail closed where the state is unknown
(F-001, F-002, F-005). A caller-declared input risk can harden the
verdict and never weaken it (F-001-a5), and recorded sensor
degradations constrain the verdict instead of failing silent
(DM-H8). These are mitigation and measurement mechanisms inside a
risk management system.

What remains with the host: the risk management system itself, which
is an organizational process: hazard identification for the intended
purpose, evaluation, testing, residual-risk judgement and its
documentation.

## Article 12: record-keeping

**Status: Provided.**

The obligation: the system shall technically allow the automatic
recording of events over its lifetime, to support identifying risk
situations, post-market monitoring and deployer-side operation
monitoring.

For every act routed through the kernel, this recording is the
default and cannot be quietly absent. Each governed turn composes a
commitment binding the tool-registry manifest, the effective
configuration, the active policy tables and the digest of the
redacted syscall journals (F-007, F-007-a5), under an explicit
format version whose changes are announced
(`COMMITMENT_VERSION`, [VERSIONS.md](../VERSIONS.md)). Every effect
syscall journals a pre-effect intent, so a missing record reads as a
ghost signal rather than as silence (F-008-a5), and the intent and
result halves are verified as a bijection where the journals are
read (P0-1-a6). Effect parameters are redacted before hashing under
a versioned redaction policy (F-018-a5). The record is exportable
and independently verifiable: one canonical encoder behind the
public `hash_ir`, with a pinned external-verifier recipe that
recomposes the commitment from the exported IR alone (DM-I2,
[IR.md](../IR.md)), a hash-linked timeline
(`examples/08_timeline_audit.py`) and deterministic replay
(`examples/02_deterministic_replay.py`).

What remains with the host: persistence and retention of the logs
the kernel emits (Article 19 for providers, Article 26(6) for
deployers, six months at minimum unless other law says otherwise),
and the recording of events outside the governed path.

## Article 13: transparency and provision of information to deployers

**Status: Partial.**

The obligation: the system must be transparent enough for deployers
to interpret its output and use it appropriately, with instructions
for use carrying the relevant information.

What ARVIS provides: a typed, documented decision contract rather
than prose to parse. The public verdict is the `DecisionStatus`
plus the structured decision block (A14-BETA-02), reasons come from
a registered reason-code registry, the stability block separates
regime from verdict and carries the certified ceiling (DM-I3), and
the result payload ships its own JSON schema
(`RESULT_SCHEMA_VERSION`). [PATH_TO_ALLOW.md](../PATH_TO_ALLOW.md)
is the honest map of why a verdict is what it is, and
[GETTING_STARTED.md](../GETTING_STARTED.md) walks the contract end
to end.

What remains with the host: the instructions for use of the host
system itself, its intended purpose, performance characteristics and
known limitations, which only its provider can state.

## Article 14: human oversight

**Status: Partial.**

The obligation: the system must be designed so natural persons can
effectively oversee it, with measures enabling them, as appropriate,
to understand its capacities and limitations, monitor operation,
interpret output, decide not to use or to override it, and intervene
or interrupt it.

The strongest mechanisms sit on the decide-and-intervene half. The
confirmation band is override-by-design: a turn in
REQUIRES_CONFIRMATION performs nothing until a bound human
validation, under a versioned confirmation format
(`examples/04_human_confirmation.py`, [VERSIONS.md](../VERSIONS.md)),
and enforcement layers may only keep or harden a verdict, so no
layer can quietly relax what a human was meant to see (F-001).
Selecting a tool never implies authority to execute it (F-009), no
effect exists without its governance (F-009-a5), and in the
PRODUCTION profile a tool declaring consent or egress requirements
is denied when the host gate is missing (F-017, F-018). On the
understand-and-monitor half ARVIS contributes the interpretable
record: `summary()`, the decision trace, the timeline, and runtime
inspection (`examples/10_runtime_inspection.py`).

What remains with the host: the human-machine interface those
overseers use, their competence and training, automation-bias
countermeasures, and a system-wide stop control (the kernel stops
governed acts; it cannot stop the host).

## Article 15: accuracy, robustness and cybersecurity

**Status: Partial.**

The obligation: appropriate levels of accuracy, robustness and
cybersecurity, consistent performance, resilience against errors and
faults, and protection against attempts to alter use or performance.

ARVIS contributes the robustness posture at the decision boundary.
Unknown state gates nothing open: an envelope that could not be
built abstains (F-005), unknown switching safety is unsafe (F-002),
an exception inside the gate forces ABSTAIN (F-006), and an empty
dwell clock vetoes instead of disappearing (DM-G1). The attack
surface at the boundary is bounded: the tool surface freezes after
bootstrap (F-004, F-019), payloads violating a declared schema never
reach the tool (F-020), late results are rejected at the deadline
(F-014), retries require declared idempotence (F-016), and archive
ingestion runs behind always-constructed guards with named,
validated limits (DM-H6). Integrity of the record is cryptographic
and deterministic (DM-I2, F-013).

What remains with the host: the accuracy of the model itself, its
adversarial robustness, and the cybersecurity of the platform around
the kernel. ARVIS measures and gates a model; it does not make one
accurate.

## Article 26: obligations of deployers

**Status: Host obligation.**

The obligation: deployers use the system per its instructions,
assign oversight to competent natural persons, monitor operation and
keep the automatically generated logs under their control for at
least six months.

ARVIS supplies the artifacts that make these duties dischargeable
rather than aspirational: the logs and commitments of Article 12
above are what the deployer retains; oversight actions are
attributable because production identity reaches both entrypoints
(`run_as`, `AuthenticatedPrincipal`, DM-S2) and confirmation records
bind the validating human's turn; monitoring has a documented
surface (`examples/10_runtime_inspection.py`,
[PATH_TO_ALLOW.md](../PATH_TO_ALLOW.md)).

## Explicitly out of scope

**Status: Out of scope.** Nothing in ARVIS addresses: classification
of the host system (Article 6); data and data governance for
training, validation and testing (Article 10); authoring the Annex
IV technical documentation (Article 11; the documents linked here
are inputs to it, not it); the quality management system
(Article 17); fundamental rights impact assessments (Article 27);
conformity assessment (Article 43); EU database registration
(Article 49); the post-market monitoring plan (Article 72); serious
incident reporting (Article 73); and the Article 50 transparency
duties toward end users (disclosure of AI interaction and marking of
synthetic content), which live in the host's user-facing surface.

## Maintenance

The status vocabulary, the disclaimer, the resolvability of every
cited decision identifier and the article list above are pinned by
`tests/docs/test_ai_act_mapping.py`; path references are checked by
the Markdown gate. Changes to this page ride the changelog. The
mapping describes the tree it ships with; for what is promised
across versions, [VERSIONING.md](../../VERSIONING.md) is the
contract.
