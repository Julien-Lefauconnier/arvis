# Glossary: ARVIS terms in standard vocabulary

ARVIS names its concepts precisely, and the price is a vocabulary an
integrator has not seen before. This page maps each term to the
nearest standard concept, says in one line where the analogy holds
and where it stops, and points to the page that owns the detail.
Read it beside [GETTING_STARTED.md](GETTING_STARTED.md); nothing
here introduces behavior, it only translates.

| ARVIS term | Nearest standard concept | The one-line truth |
| --- | --- | --- |
| Verdict bands (`ALLOWED` / `REQUIRES_CONFIRMATION` / `BLOCKED`) | Graded authorization result | An authz decision with an explicit human-approval middle state; not a content-moderation label. See [PATH_TO_ALLOW.md](PATH_TO_ALLOW.md). |
| Gate | Policy enforcement point | The ordered stack of enforcement layers that produces the verdict; layers may harden it, never relax it (F-001). |
| Commitment | Tamper-evident audit record | A hash composed from the tool registry, effective configuration, policy tables and redacted effect journals (F-007); what ran is what is committed. |
| IR (intermediate representation) | Structured audit event | The canonical, exportable record of a governed turn; the input to replay and external verification. See [IR.md](IR.md). |
| Deterministic replay | Event-sourcing replay | Re-running an exported IR reproduces the decision bit for bit, commitment included (`examples/02_deterministic_replay.py`). |
| Timeline | Append-only hash chain | Commitments linked by hash so history cannot be rewritten quietly (`examples/08_timeline_audit.py`). |
| Fingerprints (api, config, policies, registry) | Configuration drift hashes | Digests of the governing state; if one moves, a differently governed build produced it ([VERSIONS.md](VERSIONS.md)). |
| Cognitive syscall | Brokered effect boundary | Every real-world effect crosses one mediated boundary with a sealed identity context; nothing side-effects ad hoc ([architecture/EFFECT_PATH.md](architecture/EFFECT_PATH.md)). |
| Capability | Single-use authorization token | Minted per authorized effect, activated by receipt, dead after use; capability-based security in the classic sense. |
| Effect path | Egress broker | The only route from a model proposal to an executed effect; calling a tool directly bypasses everything ARVIS promises. |
| Tool manifest (`ToolSpec`) | Permission manifest | A tool's declared truth: side effects, reversibility, provider, data egress, consent required, risk budget ([tools/TOOL_AUTHORING_GUIDE.md](tools/TOOL_AUTHORING_GUIDE.md)). |
| Host | The integrating application | ARVIS is a per-turn kernel your application consults; identity, memory, models and tools stay yours ([architecture/REFERENCE_ASSISTANT_ARCHITECTURE.md](architecture/REFERENCE_ASSISTANT_ARCHITECTURE.md)). |
| Scientific state | Session measurement blob | The opaque, JSON-safe state the host threads between turns so the trajectory is measurable at all (DM-S4). |
| Projection (Pi) | Validated feature extraction | Maps raw input into the measured domain, with explicit validity rather than best effort. |
| Validity envelope | Operating design domain | The region where measurements are trusted; outside it the verdict fails closed (F-005). |
| Regime (`warmup`, `transition`, ...) | Monitor maturity phase | How much measured history stands behind the stability estimate; `warmup` means "not enough yet", by design. |
| Dwell time | Switch cooldown | Control-theory guard: a mode switch is not trusted before its dwell is served; an empty clock vetoes (DM-G1). |
| Kappa bands | Alert severity thresholds | The committed thresholds on the contraction estimate (DM-H9); part of `policies_fingerprint`. |
| Risk ceiling (`risk_ucb`) | Certified error bound | A PAC upper confidence bound on the risk rate, reported beside the empirical rate (DM-I3); statistics, not vibes. |
| Contraction monitor / Lyapunov state | Convergence monitoring | Measures whether the decision loop's dynamics are settling or drifting; says nothing about content quality ([math/README.md](math/README.md)). |
| Ratchet | One-way contract test | A test that can only tighten: surfaces, imports, coverage floors, doc claims; loosening one is a deliberate, argued act. |
| Quality gate | The canonical check target | `bash scripts/run_quality_gate.sh`, the exact set CI runs, parity enforced by test. |

Two terms deserve a warning rather than a mapping. "Cognitive OS" names
the ambition of the category, not a claim that ARVIS schedules your
processes; and nothing in this vocabulary implies content filtering:
ARVIS governs whether an act may happen and proves what governed it,
which is a different job from moderating what a model says (see
[COMPARISON.md](COMPARISON.md)).
