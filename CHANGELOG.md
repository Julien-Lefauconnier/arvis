
# Changelog

All notable changes to ARVIS are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [PEP 440](https://peps.python.org/pep-0440/)
versioning throughout the pre-1.0 series.

## [Unreleased]

### Changed

- Campaign HONEST-DOCS: the documentation claims what is measured.
  The M10 report's historical sections are stamped, section 11.4's
  inverted conclusion is retracted in place, and a new section 16
  carries the criterion-by-criterion discrimination table ('11 of
  12' overstates: two registered criteria are structurally unable to
  fail), the protocol section-5 observations the registered set
  omitted (violation rate 0.989 / 0.941 among them), and the
  registration provenance by commit hash. A gate ratchet now checks
  the report's headline numbers and the PATH_TO_ALLOW table against
  the tracked artifacts, closing the class of silently stale prose.
  M13 stops calling M10 'planned', MAPPING states the honest status
  of every equivalence row, M15 claims stability as a complement to
  alignment (content out of scope, no priority claim, real verdict
  vocabulary), and the core specification's Conformance Requirement
  3 is amended to what the implementation does (measure and disclose
  always, enforce posture available, ALLOW gated on the live
  measured adaptive margin) with a reference-implementation
  disclosures subsection (slow law off by default, fast-V decisive
  energy, conservative dwell proxy). The README gains the campaigns
  paragraph with links, executed hash literals, example 07, and
  absolute doc links.

## [0.1.0b6] - 2026-09-02

### Security

- **Canonicalization: a dataclass could hide state from the injective
  encoder.** The dataclass branch built its material from
  `fields(obj)` alone, so any attribute set on the instance beyond the
  declared fields was invisible and the private-attribute refusal was
  never reached on that path: two materially different payments shared
  a canonical hash, and a commitment or confirmation is minted from
  that digest. The map is now the declared fields union the instance
  attributes, with the same private-state refusal as a plain object,
  and an unassigned declared field is refused instead of encoded as
  None. `redact_for_commitment` no longer rebuilds tuples as lists,
  which erased a distinction the encoder tags on purpose. The
  canonical-bytes change is versioned per VERSIONING.md:
  canonicalization v4, redaction policy v6, commitment v6,
  confirmation format 5; every hash minted under the previous
  formats is explicitly invalidated.
- **The intent/result audit pair survives nesting, and an absent
  journal is no longer read as proof.** The journaled result was
  stamped with a causal id rebuilt from a sequence counter that a
  nested dispatch had already advanced, orphaning both halves and
  reporting legitimate compositions as audit-incomplete; the
  post-execution paths now journal under the id the intent was minted
  with. The commitment gatherer coerced a missing journal to an empty
  list, which satisfies the strict bijection vacuously; an absent or
  non-list journal is now audit_incomplete, while a present-and-empty
  journal stays legitimate.
- **The ZIP firewall can no longer be switched off by the
  environment.** `ZipAnalyzer` dropped its guard entirely when
  `ENV=test`, removing the file-count and size caps, the zip-bomb
  ratio check and the blocked-extension list. The guard is always
  constructed; different limits are injected at the call site. The
  advisory `supported` flag no longer deserializes to a fabricated
  True.

### Fixed

- Campaign INTEGRITY: the public integrity surface tells the truth.
  The emitted API `fingerprint` was computed eagerly during package
  import, so the fallback branch fired on every normal import and
  every result carried a bootstrap constant instead of the surface
  hash the shipped schema documents; it is now computed lazily from
  the real sorted `arvis.__all__` (the emitted value changes; no key
  changed shape, `schema_version` stays 1.0). Four 'canonical' JSON
  encoders with four parameter sets are now one
  (`arvis/ir/serialization/canonical_json.py`): the public `hash_ir`
  reproduces the committed digests verbatim, and the pinned
  external-verifier recipe recomposes `global_commitment` from the
  exported IR alone; non-finite floats refuse loudly instead of
  hashing silently into non-JSON text. The anchor is the view's
  `ir_hash`, which already used the canonical parameters, so no
  committed result digest moves; `meta.canonical_hash` moves only on
  non-ASCII content and becomes verifiable, and `decision_id` values
  change (internal mint). The stability block now carries the
  certified PAC ceiling beside the empirical rate (`risk_ucb`,
  `risk_verdict`, additive), `summary()` prints
  `RiskCeiling=1.00 (CRITICAL)` on a cold turn instead of a lone
  `Risk=0.00`, and the trace's experimental stability sub-block stops
  publishing a verdict under the key `regime`. The beta contract
  manifest is regenerated (schema fingerprint only).

- Campaign GATE-SEM: the integral audit's two semantic blockers. The
  adaptive stability layer failed OPEN on an empty dwell clock: the
  margin computation raised on `tau_d <= 0`, the gate stage
  swallowed the exception, and every veto treated the absent layer
  as no constraint, so the first threaded turn of a trajectory (the
  switching condition violated by six orders of magnitude) was the
  easiest turn to certify. 8 of 13 D-1.0 and 13 of 15 D-2.0 final
  ALLOW sat on that hole, including all 8 `nominal_feedback` ALLOW
  the SEUIL entry below celebrates; they are withdrawn. The margin
  now computes on the shared dwell floor and an empty clock vetoes
  (DM-G1); a genuinely absent layer floors ALLOW on any turn
  carrying both energies (`adaptive_unavailable`, promoted to a
  normative reason code); the validity envelope refuses to certify
  without the layer and exports `switching_safe_measured` beside the
  posture-effective value (DM-G2). Separately, the gate kernel's
  acceptance shortcut pre-empted `lyapunov_gate` on every live
  contracting turn (`stable` is literally `delta_w <= 0` there), so
  the mean-energy and DM3 worst-axis refusals never ran on real
  traffic: a state with its risk axis saturated at 1.0 earned a
  pre-verdict ALLOW. The shortcut is reserved for the injected
  scalar case it always described (DM-G3), and the stage-side
  recovery detector applies the kernel's noise floor so -1e-18 can
  no longer feed the sanctioned relaxation (DM-G4). Republished:
  D-1.0 5 ALLOW, D-2.0 4, judgments unchanged (11 of 12, 12 of 12),
  no verdict relaxed anywhere, base ABSTAIN preserved bit for bit.
  M10 section 15.

- The verdict transition trace recorded transitions that never
  happened: 431 phantom `ABSTAIN -> REQUIRE_CONFIRMATION` boundary
  entries per corpus plus thousands of no-op veto entries, about 96
  per cent of the published audit trail. Every record site is
  guarded to real changes; denial events keep their explicit
  `_denied` records; the trace grammar is pinned (no-op entries only
  from event stages, relaxation entries only from the sanctioned
  stages). D-1.0: 3145 entries to 122. Same defect class as the
  DM-P2 certificate fix.

### Added

- Campaign FIX: the audit follow-up. `docs/PATH_TO_ALLOW.md` maps
  the four conditions between a call and an ALLOW and states what
  0.1.x cannot reach; `examples/07_session_threading.py` fills the
  long-standing numbering gap and demonstrates the host threading
  contract with a fresh engine per turn. The result view exposes
  `next_scientific_state`, so that documented contract is reachable
  without reading a mutated `extra` dict. A new gate check
  (`scripts/check_broad_excepts.py`) keeps every broad except
  honest, contract pins cover the three real LLM providers, and the
  audit's gray zones (Lyapunov observer, temporal memory,
  governance evaluator) are exercised. Two transitional surfaces are
  tracked in VERSIONING.md instead of TODO markers; the tree carries
  none.

- Campaign MATH-C: corpus D-2.0 with the state-feedback nominal
  family (the contraction regime encoded in the input dynamics, the
  D-1.0 lesson applied), campaign 2 registered and executed: 12 of
  12 criteria passed, with the treatment/control contrast
  (p_contraction 1.000 on the feedback family against 0.495 on the
  exogenous control) and the adaptive layer shown to respond to
  measured contraction in both directions. The composite fast-energy
  shortcut was measured (full-W variant on D-1.0) and kept as the
  documented v0 design (DM-C1); full wiring is re-posed at DM4.

- Campaign MATH-B: the M10 empirical validation campaign executed on
  the synthetic corpus D-1.0 (56 trajectories, 1440 turns, published
  seeds). New top-level `validation/` package (excluded from the
  wheel): deterministic seven-family corpus, closed-loop pipeline
  harness, the nine metric families of M10 section 5, alpha and L_T
  estimators, pre-registered thresholds, LOT B4 sensitivity sweeps,
  and the published campaign artifacts. The M10 document now
  carries the campaign report (section 10): 11 of 12 registered criteria
  passed, the failure reported as failed; measured constants
  published report-only (no runtime default changes).

### Changed

- **Campaign SEUIL: the weak-stability floor is a registered
  contraction rate.** `delta_w_soft_threshold` was a hard-coded
  -0.05 wearing a `getattr` configuration costume; the M10 corpora
  measured that it refused ALLOW to the `nominal_feedback` family
  (engineered to contract on every turn, converging geometrically so
  its steps shrink as it succeeds) while its direct victims were
  real contractions with median |dW| 0.033. DM-S1, registered before
  the campaign run: weak iff `|delta_w| < max(0.05 * W_current,
  0.005)`, the rate being one third of the measured median
  contraction rate and the absolute floor bracketing the p05-p10 of
  observed contractions. Absolute candidates -0.01 and -0.025 and
  the status quo were each measured on both full corpora first: no
  candidate yields one ALLOW outside the healthy families, both
  registered judgments hold everywhere, and D-1.0's ABSTAIN is
  bit-identical under all of them (the filter never relaxes a
  refusal). Result: D-1.0 11 to 13 ALLOW, D-2.0 4 to 15 including
  the first 8 ever on the feedback family. The constants live once
  in `arvis/math/stability/weak_stability_policy.py`, suite-pinned;
  the context attribute remains an explicit absolute host override.
  See M10 section 14.

### Fixed

- **Campaign PROJ: the projection and switching path tells one
  story.** Three coherence defects, fixed together. The projection
  operator clamped its blending strength whenever the private
  `ctx._dv` attribute was positive, misreading the clamped drift
  magnitude as a signed divergence, exactly as the certificate had
  (the clamp fired on 85 per cent of campaign 2 turns; removing it
  moves no verdict and clears about 20 spurious boundary flags per
  corpus). The observability refresh recomputed the projection after
  the verdict and overwrote the decision certificate, so the trace
  and the IR contradicted what decided on 42 smoke turns of 42; the
  refresh is now a post-hoc attestation under distinct names
  (`post_certificate`, `projection_post_certification_level`) and
  the decision fields are never rewritten. And the dwell clock
  ticked twice per turn (regime_stage and runtime_stage both updated
  the same runtime), so the switching guard read twice the real
  dwell and `ln(J)/tau_d` was half its true value: the guard was
  satisfied with half the dwell actually served. One tick per turn
  now, post-decision; the verdicts harden accordingly (D-2.0 moves
  1277/349/6 to 1391/237/4, D-1.0 1233/185/22 to 1260/169/11, no
  ABSTAIN relaxed anywhere) and both registered judgments hold. The
  opaque scientific state blob additionally gains a `switching`
  section, so a host on the public `ArvisEngine` contract finally
  accumulates dwell across turns (a capability previously reserved
  to deep integrations owning the pipeline); older blobs load
  unchanged with a fresh clock. See M10 section 13 and
  `docs/PATH_TO_ALLOW.md`.

- **ALLOW was unreachable because the projection certificate read a
  drift magnitude as an energy derivative.** `ProjectionValidator`
  assessed its Lyapunov axis against `ctx._dv` whenever no composite
  delta was available. That attribute holds the drift score, which
  `DriftSignal` clamps to `[0, 1]` and which is therefore never
  negative, so any drift at all was published as a measured Lyapunov
  incompatibility. The gate stage writes the composite delta after
  the projection stage runs, so on the certificate the gate consumes
  the delta is always absent and the fallback was the branch taken
  on every certified turn, not an edge case. The axis is now
  assessed against the composite delta or reported unassessed in
  `checks_detail` and excluded from the certification level, the
  same treatment noise robustness and mode stability already
  receive; a present but uncoercible delta stays fail-closed. On the
  D-2.0 campaign `projection_unsafe` and
  `projection_lyapunov_incompatible` go from 1270 occurrences each
  to zero, the validity envelope goes from alive on 16 per cent of
  in-domain turns to 100 per cent on both corpora, and ALLOW becomes
  reachable: 22 turns on D-1.0 and 6 on D-2.0, all with a strictly
  negative composite delta, confined to the `nominal` and
  `long_horizon` families. The change relaxes and nothing else: the
  ABSTAIN count is bit-identical on both corpora, the registered
  judgments are unchanged (11 of 12 and 12 of 12), and adversarial
  ALLOW stays at 0.0. See M10 section 12 and
  `docs/PATH_TO_ALLOW.md`.

- **CI runs the gate instead of reimplementing it.** The lint job
  hand-copied the gate's static commands and invoked the script only
  for Bandit, so every new check had to be added twice and the newest
  one (the broad-except ratchet) was added once: a pull request adding
  a silently swallowed failure merged green and only failed at tag
  time. The gate script now exposes the granularity CI's parallel jobs
  need (`static`, `security`, `audit`, `tests`, `examples`, and `all`
  as their sum), each job selects a mode, and a ratchet
  (`tests/tooling/test_ci_gate_parity.py`) fails if a workflow ever
  forks a definition again.
- **A non-Linux runner.** The test job gains macos-latest (arm64) on
  Python 3.11: the library publishes cross-platform reproducibility
  guarantees and a real one-ulp divergence reached a developer machine
  because CI had no runner that could catch it.
- **The dependency surface.** `pyyaml` leaves the runtime dependencies
  for the dev extra (nothing under `arvis/` imports it; only the
  compliance loader does, and compliance is excluded from the wheel),
  and `jsonschema` and `numpy` gain the upper cap `pydantic` already
  had. The pip-audit suppression, previously copy-pasted into two
  workflows with its justification in only one, lives once in the gate
  and runs from an isolated environment so its transitives no longer
  move packages inside the frozen environment it audits.


- The projection domain margin measures the DANGEROUS bounds only.
  It measured the distance to the nearest bound whatever that bound
  meant, so an axis at its healthy extreme counted as boundary
  proximity: `risk.conflict_pressure` is fed by the collapse risk,
  whose healthy value is exactly its lower bound, so a system at
  zero collapse risk was read as sitting on the domain edge and
  floored at REQUIRE_CONFIRMATION. Bounds now declare which end is
  dangerous (both by default). Measured: spurious boundary flags
  fall from 1376 to 467 turns on D-2.0, zero verdict flips, both
  registered judgments unchanged.
- Telemetry emits per event: one shared try guarded the whole
  emission block and returned on the first exception, so a single
  malformed payload silently suppressed every following event of the
  turn.
- The global-stability duck default is fail-closed in both layers
  (the math layer defaulted to "ignore" while the kernel layer
  defaulted to "confirm"). Declared profiles are untouched.
- A declared no-LLM posture is state, not an error: it was captured
  into the error journal on every turn, the last noise of a nominal
  run. The nominal error journal is now empty.

- Published campaign artifacts are serialized with floats rounded
  to 12 decimals: the first third-party reproduction (macOS arm64
  against the Linux reference) drifted one double by one ulp through
  FMA reductions and broke byte-identity of a published file. The
  rounding absorbs cross-platform ulp noise; judge comparisons stay
  raw and determinism remains exact within a platform.
- The slow-drift detector measures structured slow states again. The
  scalar-era code computed abs(cur - prev) on SlowState objects that
  carry no subtraction, a TypeError swallowed as
  slow_drift_detection_failure on every structured turn; structured
  pairs now use the euclidean norm of their vector delta (the scalar
  path is kept for duck compatibility). The revived signal stays
  observability-only: it has no runtime consumer, so no verdict
  moves.

- The adaptive runtime observer reads the estimator's smoothed
  contraction factor again. Since the MATH-A snapshot rename it read
  a field that no longer exists through a silent `getattr`, so the
  whole adaptive layer (kappa bands, confirmation forcing, ABSTAIN
  veto, recovery-relaxation block) was structurally dead on every
  live path and only injected snapshots ever exercised it. The fix
  is strictly hardening (RED-first, direction verified on every
  consumer); the m10 harness now pins the layer's liveness.

## [0.1.0b5] - 2026-09-01

Four consolidation campaigns since b4, all behind a green quality
gate, the veramem consumption mirror (60/60) and the beta contract
manifest at every step: the public surface is intact, and the
mutation counter-proof on the gate's three canonical mutations holds
at 9/5/9 detections on live paths.

Campaign RELEASE (2026-09-01): release hygiene. A claims audit of all
74 Markdown documents against the tree (46 stale passages fixed:
retired context paths, deleted layers described as current, wrong
symbols and schemas; unbuilt designs now carry dated implementation
frontiers), and thirty-five behavior pins on the weakest boundary
paths (conflict-pressure host adoption, telemetry emission, IR and
finalize failure semantics, timeline commitment wire contract, the
long-memory surface, accessor fallbacks).

Campaign OBS (2026-09-01): the observability journal and the end of
the mirrors. The ctx.extra dict is no longer a hidden control-flow
bus: arvis reads its own signals from the typed journal and the
bounded sub-contexts, the extra keys remain as byte-identical
write-only exports for hosts, and two ratchets freeze the result. No
veramem-facing surface changed (mirror 60/60 at every lot; mutation
replay 9/5/9, identical to post-STRUCT).

### Changed

- **The run journal is typed storage** (PipelineJournalContext): the
  gate reason and trace accumulators (fusion_reasons,
  verdict_transition_trace), the cross-component scalars (recovery,
  vetoes, kappa band and one-shot latch, warnings, escalations,
  structural risk, input risk, confirmation override), the verdict
  provenance ledger and the gate fusion trace. The extra exports are
  aliased to the same objects, so host-visible content is unchanged;
  accessors adopt pre-seeded export lists and keep duck-tolerance
  contracts holding.
- **The root context facade is retired**: the 43 remaining mirror
  properties on CognitivePipelineContext and the 36 dead second-level
  mirrors on PipelineScientificContext are migrated and deleted.
  Typed callsites use the bounded sub-context paths; duck-tolerant
  callsites go through scientific_accessors (uniformly duck-tolerant),
  the new observability_accessors and tooling_accessors; the math
  layer chains getattr on the canonical shape and stays import-free
  of the kernel.
- The gate confirmation flag consumes the real declared
  ctx.conflict_pressure through the same canonical threshold function
  as the confirmation stage (decision DS4a; the historical read was a
  phantom attribute, 0.0 on every run), and DecisionTrace.conflict
  carries the declared conflict channel instead of an extra key
  nothing writes (DS4b). Hardening-only, pinned by property tests.
- build_test_context seeds the canonical tension channel
  (observability.diagnostics.system_tension); the historical dynamic
  attribute reached no reader, so tension seeded by tests now
  actually flows into the projection (decision DS5; no pinned
  expectation moved).

### Removed

- The prepare/finalize lifecycle latches left the extra bus for
  declared private fields: a host-seeded key can no longer skip
  preparation or inject a foreign cached result past the gate; the
  confirmation override propagated into the serialized IR record now
  comes from the journal only (the ALLOW-with-vetoes override
  injection is closed). The dunder extra keys remain as write-only
  exports.
- Seventeen scientific accessors with zero callers.

### Added

- **The extra-read ratchet** (tests/contracts/test_extra_read_ratchet):
  a parent-aware AST scan of arvis/ resolves local aliases and
  classifies every read of an extra mapping; the 49 surviving
  (file, key) pairs are frozen with their category (host-input,
  accumulator export, accessor fallback, mapping-only boundary, the
  kappa latch) and the list is enforced in both directions.
- The facade ratchet becomes a floor with a shadow guard: the context
  defines no properties at all, and no retired mirror name may
  reappear as a dynamic instance attribute after a default run.

Campaign STRUCT (2026-08-31 / 2026-09-01): structural consolidation.
The audit's frozen dead weight is gone, the hot path is typed against
the real objects, and the mirror/extra channels have a doctrine. No
veramem-facing surface changed (mirror 60/60 at every lot).

### Removed

- **The dead-code burn-down is complete**: 91 unreachable modules at
  the audit, 0 pending today. This campaign deleted the standalone
  conversation orchestration layer (38 modules), the unwired
  predictive/probabilistic math layer (14) and the remaining dead
  chains (32: the kernel adapter rule engine, dead LLM contracts and
  observability providers, the lexicon and dead linguistic acts,
  runtime snapshots, the raw signal layer, redaction, orphan
  cognition flows), each verified importer-free. The import-closure
  ratchet now lists only three deliberate test harnesses
  (projection_api, the in-memory VFS repository), and `arvis.api.*`
  joined the closure roots as the curated public namespace.
  KERNEL_ADAPTERS.md and the linguistic spec carry dated
  implementation frontiers instead of describing deleted code.
- The pipeline's delegation-only facades (Iteration, StageExecution,
  Execution, Lifecycle, Compatibility, ExecutionSync services), the
  executor's speculative signal machinery (pipeline_contract.py) and
  its impossible duck-typing guards, the CognitiveOSInternals mixin
  (merged into CognitiveOS), ControlInertia's phantom smooth() API
  and its backward-compatibility alias. The kernel pipeline's
  12-module import cycle is gone; the repository import graph's
  non-trivial SCCs drop from 6+ to 4, none in kernel/pipeline.
- Thirteen mirror properties (the decision/execution/policy family)
  left CognitivePipelineContext after their reader sites migrated to
  the sub-contexts, following the facade ratchet's protocol.

### Changed

- **The twenty pipeline stages are typed against the real
  CognitivePipelineContext and CognitivePipeline** (they ran on
  Any/Any). Typing surfaced 47 real findings, each resolved at its
  source: the stage-published working state is now declared on the
  context (conflict, conflict_pressure, temporal channels, memory
  modes, kappa_band, adaptive_control, slow_divergence,
  regime_confidence, the gate's stability_certificate and
  system_confidence, and the private mirror scalars); the syscall
  layer keeps ONE protocol per concept
  (kernel_core/syscalls/protocols.py) instead of fourteen local
  re-declarations, and types its handlers nominally.
- **The gate consumes the canonical scientific context**: the
  gate-entry hydration walk (an identity on real contexts) is
  reduced to its one live copy (the slow/symbolic bridge into the
  composite slots) plus the compliance injection channel; the
  composite evaluation stops double-writing through the accessor
  layer; the drift channel lives only in its sub-context.
- **ctx.extra carries its doctrine**: a host boundary channel
  (documented keys; controls never ride it) plus the run
  observability journal, whose migration into typed observability
  contexts is the named follow-up.
- CognitiveControlEngine.compute is seven named, independently
  degrading steps (485 to 290 lines, public signature unchanged);
  GateObserver.build takes one typed GateObservation instead of
  eighteen keyword parameters.
- The scheduler's anti-starvation mechanism is pinned by multi-tick
  properties: budget depletion (not aging, which cannot close a
  priority gap) is what guarantees every budgeted process runs.

### Fixed

- **The temporal stage owns the temporal channel (decision DS3,
  RED-first)**: the control stage no longer overwrites the computed
  TemporalPressureSnapshot/TemporalModulation with an ad-hoc binary
  object whose 1.2 multiplier bypassed the [0, 1] clamp. A timeline
  can now only keep or tighten epsilon (monotone hardening). The
  invariant-free duplicate TemporalModulation class in
  temporal_regulation.py is unified with the canonical clamped one.
- The uncertainty-intent path was dead by type error (the mapper
  requires an UncertaintyFrame; the control stage passed an
  UncertaintySignal and a broad except silently produced None on
  every run): the channel is declared, honest, and the impossible
  call plus its orphaned mapper are gone.
- Two same-name class collisions resolved where the wrong one could
  bind: ConflictSignal (the raw cognition event vs the math pressure
  signal; the context channel carries the math signal) and
  TemporalModulation (above). A phantom gate read
  (ctx.conflict_signal, never written, contribution 0.0) is now an
  explicit constant with the wiring decision recorded in the
  campaign report.

Campaign MATH-A (2026-08-31): the default engine measures its own
science. Resolves the audit's central finding (the Lyapunov machinery
was wired but never evaluated on any default path).

### Added

- **The contraction monitor is the default core model**
  (`CognitiveOSConfig.core_model`; explicit `None` opts out). Every
  governed run measures a four-axis Lyapunov state, its energy V, a
  drift score, a PAC-certified risk ceiling and an empirical regime;
  `stability_score = 1 - V`; a view with no conclusion reports honest
  absence. The monitor declares its calibration in a
  `governance_manifest()` bound into the run commitment.
- **Threaded scientific state is a public contract**:
  `run(..., extra={"scientific_state": s})` in,
  `extra["scientific_state_next"]` out; documented in
  `docs/architecture/RUNTIME_LIFECYCLE.md`, runnable in
  `examples/12_threaded_stability.py`, pinned by
  `compliance/internal_invariants/core/test_threaded_state_contract.py`
  (channel keys, JSON round-trip, deterministic trajectories, safe
  degradation).
- **Worst-axis refusal guard** in `lyapunov_gate`
  (`axis_abstain_threshold`, default 0.95): a single saturated axis
  refuses even when the convex mean dilutes it (decision DM3).
- Live-path gate properties (Hypothesis): kernel totality,
  refusal-first over the whole input space, declared-risk bands held
  at every trajectory depth (DM1), fail-closed on a raising core
  model. Per-package ratcheting coverage floors for the decisive
  packages (`scripts/check_module_coverage.py`, gate + CI).

### Changed

- The contraction estimator keeps divergences visible: reporting floor
  -1.0 (was 0.0, which made a x100 blow-up look neutral), divergence
  streak counted on the raw value; one divergence caps the regime at
  "marginal", a streak forces "unstable". The module states it
  estimates the EMPIRICAL contraction factor, distinct from A12's
  theoretical kappa_eff.
- `CompositeLyapunov`: the docstring tells the truth (W is a bounded
  score); `delta_W` returns None across a target-availability change
  instead of a meaningless number; `check_small_gain` requires its
  constants (the old defaults made it pass by construction).
- Assumption A5 restated in class-K form (the quadratic bounds were
  unsatisfiable by the implemented V; exponential-rate results belong
  to the quadratic family). `docs/math/README.md` indexes the corpus
  with the implementation frontier; M13 carries the current frontier.

Cleanup campaign (2026-08-31): behavior, plumbing and documentation
honesty. No new features; the deep math track (wiring the contraction
monitor into the default engine, revising assumptions A5/A12) is
deliberately not part of this pass.

### Security

- **Gate: refusal-first ordering.** The stable-flag fast path no longer
  short-circuits the collapse-risk and CRITICAL-mode refusals
  (previously `stable=True` with `delta_w=-1e-12` produced ALLOW at
  `collapse_risk=0.99` in CRITICAL mode).
- **Gate: bounded, capped recovery.** Recovery detection requires a
  real improvement (`RECOVERY_MIN_IMPROVEMENT = 1e-3`), the kernel
  reports recovery but never relaxes its own verdict, the policy
  relaxation shares the abstain threshold
  (`COLLAPSE_ABSTAIN_THRESHOLD`), and every recovery relaxation caps at
  REQUIRE_CONFIRMATION (the former `recovery_to_allow` jump is gone).
- **Fusion pruned to observation-only.** The multiaxial fusion's dead
  composite/global axes (never wired in production; one branch relaxed
  REQUIRE_CONFIRMATION to ALLOW against the strictness order) are
  removed; enforcement lives in the policy layer.
  `MultiaxialInputs` loses `use_composite`, `global_action`, `delta_w`.

### Changed

- **Honest observability.** `StabilityView` axes are optional; a run
  that measured nothing reports `None`/`n/a` instead of fabricated
  zeros, and `summary()` shows the caller-declared risk under its own
  `DeclaredRisk` label. The consumer schema already allowed null.
- **Reflexive introspection describes reality.** The world-model
  introspector (four phantom modules) is deleted; the math declaration
  names only real import paths with an explicit execution status
  (`default_path` vs `host_driven`); static declarations say so.
- **README shows real outputs**, the actual thresholds (0.4/0.8), the
  pure-payload precondition, a Runtime profiles section (production is
  harden-only), and a Validation section aligned with what the suite
  establishes.
- LICENSE restored to the canonical Apache-2.0 text (the distributed
  copy was missing the final paragraph of section 4 and the APPENDIX);
  `license-files` no longer ships `AUTHORS_NOTE.md` (moved to docs/).
- Canonical contact unified to admin@veramem.com.
- The VeraMem document (previously VERAMEM_CASE_STUDY.md) renamed to
  `docs/integration/VERAMEM_INTEGRATION_PATTERN.md` and reframed (author's own host, not
  an independent adoption); the ARVIS-vs-LLM comparison document removed pending a
  comparison that names real comparables.
- Reason-code registry: 15 codes emitted by no code path are now
  `reserved` instead of normative/informative.
- RFC 2119/8174 boilerplate added to every spec; the spec hierarchy
  declares the status of the two out-of-stack standard documents.

### Removed

- `arvis/interfaces/` and `arvis.kernel.kernel_contract`
  (zero implementations, usages and tests).
- `compute_public_api_fingerprint` / `PUBLIC_API_FINGERPRINT`
  (unconsumed clone of the shipped fingerprint).
- Duplicate snapshot dataclasses in `arvis/stability/` (the
  `arvis.math.observability` copies are the single source; the public
  import path re-exports).
- Two fake adversarial test files whose assertions could not fail.

### Tests

- New ratchets: README outputs executed and compared
  (`tests/docs/test_readme_outputs.py`), reason-code registry
  bidirectional check, import-closure burn-down
  (`tests/contracts/test_import_closure.py`, 91 entries frozen),
  Markdown path references and path headers verified in the gate and
  CI (50 wrong headers fixed).
- Gate safety properties pinned red-first
  (`tests/math/gate/test_gate_safety_ordering.py`); strict-sign
  assertions on `delta_W`.

## [0.1.0b4] - 2026-07-26

Corrective beta release restoring the not-found / denied distinction that the
0.1.0b3 strict resolver doctrine erased, while closing the
time-of-check/time-of-use gap at its root for `vfs.get` and preventing an
authorization-time absence from reaching any later VFS read or effect. The
guiding principle is that fail-closed does not mean fail-opaque. The public
surface is unchanged: `HOST_API_VERSION` stays `1.0`, no `host_api` module
moved, and the beta contract manifest is unchanged (the new `ResolvedAccess`
type is internal to the kernel, not exported).

### Security

- Read single-read (`vfs.get`): the access resolver reads the target item once,
  to authorize against its real owner, organization and scope, and hands that
  same item to the syscall body, which returns it WITHOUT a second read. What is
  authorized is exactly what is returned. This closes the reproduced read
  time-of-check/time-of-use path (B3-VFS-01) at its root rather than by refusing:
  a body that re-read could receive a different resource from a live store than
  the one authorized. The generic mechanism is a new internal
  `ResolvedAccess(context, resource, lookup_error)` a resolver may return in
  place of a bare `AccessContext`; it is additive and backward compatible
  (resolvers that read nothing keep returning `AccessContext`, treated as no
  carried resource), so non-VFS resolvers are unchanged.
- Expected-error terminal handoff (all item/parent VFS syscalls): when the
  resolver observes a normal missing-item or missing-parent condition, it
  carries that exact terminal outcome to the body. The body maps the precise
  public VFS code WITHOUT reading or mutating the service. An item that appears
  after the authorization miss is therefore never returned, renamed, moved or
  deleted, and a parent that appears after the miss never receives a new child
  or ZIP import. Kernel-reserved handoff arguments are rejected when supplied
  by a caller, and an ambiguous handoff carrying both a resource and an error
  cannot be constructed.
- Anti-enumeration preserved by the denied case, not by erasing not-found: a
  principal without access to an EXISTING item is denied by the owner,
  organization and scope policy (`access_denied`), indistinguishable from any
  other denial, so it cannot tell "exists but forbidden" from "does not exist".

### Changed

- Resolver finesse restored (revises b3 A-03): the item resolver now
  distinguishes an EXPECTED VFS condition (item or parent not found, ...) from an
  UNEXPECTED failure. An expected condition no longer becomes an opaque
  `authorization_failure`; the resolver stays neutral for the decision and the
  syscall body maps the SAME terminal condition to its precise code
  (`vfs_item_not_found`, `vfs_parent_not_found`, ...) WITHOUT touching the
  service again. For `vfs.get`, a successful lookup similarly carries the exact
  authorized item to the body. This gives finesse and closes the expected-error
  TOCTOU at once for reads and effects. An UNEXPECTED failure still denies
  fail-closed with `authorization_failure`, so the indeterminate case that b3
  A-03 targeted stays closed. This corrects the b3 doctrine, which propagated
  EVERY lookup failure (expected included) and so erased the legitimate
  not-found / denied distinction.
- Mutation atomicity is documented as the store's responsibility, not the
  kernel's (VFS spec 23.2) only after the resolver actually found and authorized
  the target. A write syscall then mutates by id; ARVIS is a governance kernel,
  not a transactional engine, and does not fake store-level atomicity by
  passing a pre-read snapshot to the mutation (which would only displace the
  window while creating a false assurance). A host requiring strict
  serializability provides it in its repository (compare-and-swap or
  transaction). Conversely, a resolver miss is terminal and never reaches the
  mutation, so "absent during authorization, present during dispatch" cannot
  become an effect.

### Notes

- A host on 0.1.0b3 that translated a missing item as an authorization failure
  will now receive the precise `vfs_item_not_found` (and the sibling parent and
  name codes) again, as it did before 0.1.0b3. A host that had adapted to the b3
  behaviour should expect the not-found codes to return.

## [0.1.0b3] - 2026-07-25

Corrective beta release closing the six findings of the independent audit of
the VFS resource-scope feature. It makes narrower-than-organization scopes a
governed isolation boundary in the kernel, with the security property enforced
and verified rather than assumed. The public surface is unchanged:
`HOST_API_VERSION` stays `1.0`, no `host_api` module moved, and the beta
contract manifest changes only to record `VFSItem`'s field order and unchanged
public methods.

### Security

- `VFSItem.resource_scope` is now honoured as an isolation boundary across the
  whole VFS surface, not merely carried. A resource that carries a scope is
  reachable only when the principal's grants cover that scope (opaque, never
  parsed), cumulatively with organization membership and the required
  capability.
- Backward-compatible constructor (A-01): `resource_scope` is the LAST field of
  `VFSItem`, so every positional constructor call written before scoped grants
  existed builds the exact same object. New callers pass the scope by keyword.
- Metadata preservation on reconstruction (A-02): a private
  `VFSItem._with_changes(**changes)` primitive returns a copy with only the
  named fields changed and every other field preserved. `rename` and `move`, in
  both the reference repository and the service fallbacks, use it, so they can
  no longer drop `owner_id`, `organization_id` or `resource_scope`. An unknown
  field name raises rather than building a divergent object.
- Resolver fail-open closed (A-03): on ANY metadata lookup failure, including an
  expected VFS domain error such as `VFSItemNotFoundError`, the item resolver no
  longer fabricates a resolved, caller-owned, unscoped resource. It propagates
  the exception, and the handler turns it into a fail-closed
  `authorization_failure` refusal before the syscall body can perform a second
  lookup. This closes the reproduced time-of-check/time-of-use path where the
  first lookup failed and a second returned a foreign scoped resource.
- Governed collections (A-04): `vfs.list` and `vfs.tree` evaluate every returned
  item against the full policy, not just the caller's own scope at the syscall
  boundary. Only accessible items survive; an item whose evaluation errors is
  excluded, never included by default, and the result is never widened. For
  `vfs.tree` the flat list is filtered before the tree is built, so no forbidden
  node is ever materialized. Each item is judged under the REAL calling syscall
  (`vfs.list` or `vfs.tree`), so a host policy that governs the two operations
  with distinct capabilities is applied correctly and neither borrows the
  other's grant.
- Both-sided move governance (A-05): `vfs.move_item` reads the source and the
  destination parent before any mutation and refuses, with no partial mutation,
  a move into a parent the caller may not write, a move that crosses
  organization or scope (opaque equality), a move of a scoped item to the
  unscoped root, or a move with an indeterminate source or destination. A
  cross-scope transfer is not an ordinary move.
- Impose-and-verify creation inheritance (A-06): a child inherits its parent's
  organization and scope as a governed invariant CENTRALIZED in `VFSService`,
  the common boundary of every creation path. The service derives the parent's
  context, imposes it on the repository call, then verifies the created item
  carries it. A missing read-after-create result is no longer replaced by a
  synthetic item. Unreadable or non-conforming creations are deleted, deletion
  is verified, and the creation is refused. A failed or ineffective rollback is
  no longer swallowed: it produces the distinct
  `inheritance_rollback_failed` refusal. Because the invariant lives in the
  service, the ZIP import path (which reaches the service directly, without a
  creation syscall) inherits the parent's organization and scope on every
  descendant. Root creation inherits nothing and stays unscoped. Host
  persistence adapters remain responsible for atomic creation and reliable
  read-after-create/delete semantics.

### Added

- `VFSItem` gains an optional `resource_scope: str | None = None` field, the
  item's opaque narrower-than-organization scope. The item access resolver
  copies it verbatim into the `AccessContext`, where the injected scope rule
  decides coverage; ARVIS never parses it. Additive and backward-compatible:
  the field defaults to `None` (a scopeless item, the pre-scoped behaviour), so
  a host adapter that does not set it is unchanged. `HOST_API_VERSION` stays
  `1.0` per the additive-changes-remain-free rule (VERSIONING.md); the beta
  contract manifest is regenerated to record the new field.
- Repository creation methods accept optional inherited `organization_id` and
  `resource_scope` (default `None`, behaviour-neutral). `VFSService` derives
  both values from the parent and always passes them to the repository; its own
  public creation methods deliberately do not accept caller-supplied scope.
  Neither contract is part of `host_api`.
- An adversarial isolation suite (`tests/kernel_core/access/`) locking each
  finding: positional compatibility, reconstruction preservation, end-to-end
  denial on expected and unexpected indeterminate lookups, no collection leak,
  cross-scope move refusal, creation-inheritance verification and explicit
  failed/ineffective rollback reporting.
- Installed-wheel black-box compliance covers the legacy positional
  `VFSItem` constructor, exact-scope authorization, missing/wrong-scope refusal
  and the expected-error-then-foreign-resource A-03 regression.

### Changed

- Package version moves to `0.1.0b3`; README, source fallback and public status
  are coherent with the beta.
- Item-referencing syscalls now return `security_error` with
  `reason_code=authorization_failure` when the item or parent cannot be
  resolved during authorization, including ordinary not-found conditions.
  This intentional fail-closed change avoids revealing whether an inaccessible
  identifier exists and prevents a second lookup after indeterminate metadata.
- `ARVIS_ACCESS_SPEC_V1` and `ARVIS_VFS_SPEC_V1` document the resource-scope
  invariants: opacity and the injectable coverage rule, the cumulative
  organization + capability + scope condition, the None-is-covered semantics,
  the resolution-failure-is-not-an-unscoped-resource rule, per-item collection
  filtering, both-sided move governance, impose-and-verify creation inheritance,
  and the obligations a host-supplied VFS service must uphold.
- Following an independent counter-audit of the b3 candidate, three isolation
  defects were closed before release: the resolver now denies on an
  indeterminate lookup instead of trusting the body to fail (A-03,
  time-of-check/time-of-use), creation inheritance was centralized in
  `VFSService` so the ZIP import path can no longer drop scope (A-06), and the
  per-item collection filter now judges each item under the real syscall name so
  `vfs.tree` cannot borrow the `vfs.list` capability (A-04). The candidate was
  neither tagged nor published before these closures.

## [0.1.0b2] - 2026-07-25

Corrective beta release. It closes the non-finite input-risk defect found by
the independent audit of the published `0.1.0b1` artifact and adds a reference
integration path for developers adopting ARVIS.

### Security

- Explicit numeric risk now accepts finite values only. `NaN`, positive
  infinity and negative infinity raise at the risk boundary and force
  `ABSTAIN/BLOCKED` in local, research, test and production postures instead of
  being clamped to `0.0` and allowed.
- The fail-closed path detaches the caller's mapping, replaces only the invalid
  internal risk scalar with JSON `null`, and refreshes the frozen input IR.
  The caller's object is never mutated; exported IR, composed commitments and
  reflexive output remain strict-JSON serializable.
- Reflexive fingerprinting, cognitive IR serialization and result-view IR
  hashing now use `allow_nan=False`; a non-finite value cannot enter canonical
  material as a non-standard JSON token.
- The installed-wheel black-box suite pins all three non-finite cases:
  `BLOCKED`, sanitized IR, strict result JSON and a valid reflexive attestation.

### Added

- A stack-neutral
  `docs/architecture/REFERENCE_ASSISTANT_ARCHITECTURE.md` explaining ARVIS as
  the governance boundary inside a complete sovereign assistant.
- A concise `docs/integration/VERAMEM_INTEGRATION_PATTERN.md` (published
  at the time as VERAMEM_CASE_STUDY.md, renamed 2026-08) mapping a host
  application onto that architecture without turning VeraMem infrastructure
  into an ARVIS dependency.
- `examples/11_governed_assistant.py`: registration, registry freeze, an
  allowed read and an external send awaiting confirmation. The example
  deliberately performs no direct tool effect and points to the governed
  syscall path.
- The release workflow creates an idempotent GitHub Release after PyPI
  publication and attaches the exact wheel, sdist and CycloneDX SBOM.

### Changed

- Package version moves to `0.1.0b2`; README, source fallback and public status
  are coherent with the beta.
- PyPI's Changelog project URL now targets the versioned `CHANGELOG.md`.
- The deprecation policy now states one unambiguous rule: one published beta
  of overlap during beta, at least one minor release after stable `0.x`.
- The examples smoke gate now runs eleven examples.

## [0.1.0b1] - 2026-07-24

ARVIS enters beta: the beta contract, as closed by the a15, a16 and a17
campaigns and confirmed by four independent audits. No functional
rupture from a17; the surface freeze becomes policy.

### Changed

- Development status moves to Beta (PyPI classifier, README). The
  public surface (`arvis.__all__`, the stable `host_api` modules, the
  shipped serialization contract and the attestation canonicalization)
  is stabilized and covered by the deprecation policy documented in
  `VERSIONING.md` (new "Beta series" section).
- Migration from a17: none required. Consumers pinning `0.1.0a17` can
  move to `0.1.0b1` unchanged.

### Fixed (hardenings from the a17 audit, 16.3)

- `to_json()` is strict JSON (`allow_nan=False`): a non-finite float
  fails loudly instead of emitting invalid `NaN`/`Infinity` tokens,
  with a negative proof.
- The attestation verifier absorbs exceptions from hostile container
  subclasses (boundary fail-closed), its docstring states the expected
  ordinary-JSON input, and the residual "canonicalization 1.0" line is
  corrected to 2.0.
- The black-box wheel suite imports the contract loader from the
  official root surface and gains two attestation scenarios: a valid
  payload verifies from the wheel and a forged field fails; an unknown
  canonicalization version is refused (13 tests).
- The constructor-invariant comment states its exact scope (unknown
  commitment policy).

## [0.1.0a17] - 2026-07-24

The final contractual closure before beta, fixing the two defects
reproduced by the independent a16 audit. No new subsystem.

### Fixed

- Total public result conformance (a16 blocker 1): the public no-trace
  path (`CognitiveOSConfig(enable_trace=False)`) emitted
  `commitment_policy=None`, rejected by the shipped schema. The minimal
  view now carries the actually configured audit policy, an explicit
  `trace_disabled` reason and the exact F-015 degradation semantics.
  Contract invariants move into the constructor (`commitment_policy`
  typed `str`, enum-aligned default, `__post_init__` validation): an
  out-of-contract `CognitiveResultView` cannot exist. The synthetic
  contract test is replaced by real end-to-end no-trace runs under both
  policies, plus the property that every result produced by `run`,
  `run_as`, `ask`, `replay_recomposed` and `replay_verified` validates
  the shipped schema; the wheel black-box suite gains the no-trace
  scenario.
- Complete attestation verification (a16 blocker 2): `verify` rebuilds
  the full attestation and compares the entire embedded block to its
  recomputed form (exact key set, exact metadata values, constant-time
  fingerprint comparison). The audit's eight forgery probes, all of
  which previously verified True, now all fail and are pinned as
  parametrized tests. Fail-closed is real: every malformed input shape
  returns False instead of raising.

### Changed

- Attestation canonicalization 2.0: `mode` and `canon_version` become
  attested members of the canonical source, so neither can be
  rewritten, even consistently across the payload and the block,
  without changing the fingerprint; unknown canonicalization versions
  are refused before any computation.
- Contract surface: `load_result_schema` and `RESULT_SCHEMA_VERSION`
  are exported at the root (11 symbols); the beta manifest gains a
  constant branch freezing the exact promised version values.
- `docs/VERSIONS.md` moves to nineteen constants with the consumer and
  reflexive contract table; `docs/REFLEXIVE.md` documents
  canonicalization 2.0 and the explicit "structural integrity, not
  authenticity" boundary.

## [0.1.0a16] - 2026-07-24

The final release candidate before beta, closing the two contractual gaps
and the retained findings of the independent a15 audit. No new subsystem.

### Added

- Versioned serialized result contract (A15-BETA-01): a JSON Schema
  (draft 2020-12, `schema_version` 1.0) ships inside the package at
  `arvis/api/contracts/cognitive_result_v1.schema.json`; its SHA-256 is
  frozen in the beta contract manifest, `to_dict()` carries
  `schema_version`, eight contract tests validate the three risk bands
  plus the no-decision view with negative proofs (removed key, renamed
  key, changed type), and the black-box suite validates the schema
  loaded from the installed wheel. `VERSIONING.md` documents the
  deprecation rule; open-structure blocks are explicitly experimental.
- Verifiable reflexive attestation (A15-BETA-02): the attestation is
  excluded from its own fingerprint and `exposed_views` is carried
  natively by the payload, so the final public payload verifies
  directly. The canonicalization is documented and versioned
  (`canon_version` 1.0). New public API
  `arvis.verify_reflexive_attestation(payload)` (root surface
  deliberately extended to 9 symbols), fail-closed, with eleven tests
  covering tamper detection on every attested surface.
- Editorial hygiene ratchet (`tests/contracts/test_docs_hygiene.py`):
  exactly one H1 per mathematical document with mid-line duplicate
  title detection, and zero conversational session residue in `docs/`.
- CI `min-deps` job: the published lower bounds installed exactly, full
  suite on 3.11. CI `wheel-compliance` job: black-box compliance
  against a freshly built wheel on every push and pull request.

### Changed

- `ReflexiveAttestation.exposed_views` becomes a tuple: the frozen
  dataclass is genuinely immutable and `immutability` is now accurate;
  `deterministic` is documented as purity over the canonical source,
  with no cross-run identity claim.
- `docs/math/M4_adaptive_stability.md` deduplicated (283 to 139 lines): the two pasted
  versions were proven strictly identical; the French LLM-session
  dialogue is purged.
- Scientific wording aligned: the stability specification announces its
  four figures as planned, M11 moves the empirical characterization of
  Pi_ctrl to prospective wording, M13 replaces "Theoretical / proven"
  with "Conditional results and proof skeletons".
- README example 09 renamed "Multi-engine hosting"; three
  documentation statuses updated from a11 to a16; the CI dependency
  audit comment now matches its blocking command.
- numpy lower bound raised to >=2.4.1 (2.4.0 was yanked from the
  index).

## [0.1.0a15] - 2026-07-24

The final contract campaign before beta, closing the four blockers and the
retained P1 findings of the independent a14 audit. This release makes the
frozen surface real: no reference obtained from the registry can move the
validated surface, the central result type is itself part of the contract, the
lifecycle doctrine is univocal and mechanically enforced, the science corpus
claims nothing it has not executed, and the published artifact is the proven
artifact.

### Security

- The tool registry TOCTOU window is closed (A14-BETA-01): verified_spec()
  never hands out the private capture; every governed read returns a fresh
  ToolSpec rebuilt from the pinned canonical bytes, caller-owned and atomic
  with respect to concurrent schema mutation. The audit's concurrent probe is
  replayed as a deterministic barrier-based test and now reports
  prepare_accepted_diverged_surface=False.
- The release gate runs in the same locked environment as CI (A14-P1-03):
  release.yml installs requirements/gate.lock with the package on top in
  --no-deps, replays the blocking dependency audit with the same documented
  exception, and runs the normative black-box suite against the exact wheel
  that will be published (A14-P1-02), in a pristine venv where the repository
  is not importable.

### Changed

- CognitiveResultView and the new typed DecisionStatus are exported from
  arvis and host_api.engine (A14-BETA-02); the view gains a typed .status
  property (ALLOWED / REQUIRES_CONFIRMATION / BLOCKED / NONE, the product's
  established vocabulary), to_dict()["decision"] becomes a structured block
  (status, flags, denied_reason) and is never a repr, and the decision field
  is typed ActionDecision | None. Repr parsing is purged from the whole
  repository: examples, doctrine tests and the black-box suite read
  result.status.
- The beta contract manifest pins default values canonically and the
  qualified identity of default_factory functions, for dataclasses and
  pydantic models, and gains a root_api section freezing every arvis.__all__
  symbol, CognitiveOS included; proven deterministic across Python 3.11/3.12
  and pydantic 2.8/2.13.
- The lifecycle doctrine is univocal (A14-BETA-03): one instance per governed
  turn, discarded; sequential reuse works, is exercised by the isolation
  tests as an isolation proof, accumulates unbounded state and is not
  recommended; concurrent reuse is forbidden. Example 09 builds a fresh
  engine per decision through a host factory, and an AST contract test keeps
  every example on the pattern.
- Runtime dependency minimum bounds are tightened to the versions actually
  proven by the gate (A14-P1-07): jsonschema>=4.26, pyyaml>=6.0.3,
  numpy>=2.4, pydantic>=2.8.

### Fixed

- The reflexive layer works on the real CognitiveState (A14-P1-01):
  _safe_serialize learns dataclasses, enums, tuples and datetimes, with a
  deterministic opaque marker for live objects (the in-state SignalJournal
  broke the attestation's deepcopy before json.dumps ever ran). The nominal
  path now produces the reflexive payload and its attestation; the three
  skipped integration tests are hard-asserting passing tests, a unit test
  replays the audit probe, and REFLEXIVE.md documents the serialization
  contract.
- The mathematical corpus numbering is coherent (A14-BETA-04): M13, M14 and
  M15 carried titles shifted by two; all are renumbered without renaming
  files. M13 classifies M10 as a planned protocol everywhere, states precise
  conditionality (T6-T9 proven, offline Phase A, T10 hypothesis) and carries
  an honest final statement; M15's comparative table says planned for M10;
  M5 no longer claims a nonexistent runtime validation stack. A whole-corpus
  sweep, root files included, reclassified the stability-frontier grid
  exploration of ARVIS_STABILITY_CORE_SPECIFICATIONS as planned, replaced
  the four missing figure embeds with explicit notes, and turned the linear
  two-regime example claim into an executed, seeded test
  (tests/math/test_linear_two_regime_example.py).
- CONTRIBUTING.md is true as written (A14-P2-02): the documentation corpus
  is purged of its 176 em-dashes, the remaining French comments in tests are
  translated, and a repository-wide ratchet
  (tests/contracts/test_no_em_dashes.py) keeps em-dashes out for good.


## [0.1.0a14] - 2026-07-24

The beta contract campaign, closing the four blockers of the external a13
audit (BETA-01 to BETA-04) and its P1 findings. This release freezes what a
host can rely on: the tool surface is deeply frozen, the engine lifecycle is
the documented one, the public contract is pinned by a manifest, the science
documents say exactly what is measured, and the compliance suite proves the
installed wheel.

### Security

- Deep freeze of the tool registry (BETA-01): tool specs are captured and
  sanitized at registration (canonical bytes, private rebuilt copies), the
  manifest is snapshotted at freeze() and the fingerprint is never recomputed
  from live objects. Authorization, dispatch and policy evaluation read the
  surface through an integrity-checked path and refuse fail-closed on any
  divergence (frozen_surface_diverged). Non-canonicalizable schemas,
  non-ToolSpec specs and non-finite values are refused at registration,
  atomically.
- Proof structures are deep-frozen on the commitment paths (P1-04, targeted):
  the IR witness, its hash and its envelope derive from a single canonical
  serialization (hash byte-identical, replay preserved), and the projection
  certificate snapshots its detail map at construction.
- The dependency gate is locked and audited (P1-03): requirements/gate.lock
  freezes the full transitive environment, CI installs from the lock, test
  plugins are pinned, and pip-audit is a blocking CI step with an explicit
  exception policy in SECURITY.md.

### Changed

- run(), run_as() and ask() return a single public type,
  CognitiveResultView (BETA-02); the legacy no-trace mode returns a minimal
  view carrying the decision only, since no trace or commitment can exist
  there. ArvisEngine carries explicit signatures with real types; passing
  both an explicit config and keyword arguments now raises TypeError.
- TimelineView.entries is a tuple.
- The compliance tree is split (P1-01): the former suite becomes
  compliance/internal_invariants (white-box, documented as such) and the new
  normative compliance/blackbox suite exercises only the public surface, with
  versioned scenarios, wheel provenance enforcement and an authenticated
  replay round-trip; scripts/run_blackbox_against_wheel.sh proves it against
  the built wheel in a pristine environment.
- The five projection test files use a module-level seeded RNG: the Phase A
  corpus is reproducible bit-for-bit (BETA-04).
- Synthetic compliance certificates are faithful to the runtime:
  noise_gain_estimate is null, never a fabricated 0.0.

### Added

- arvis.host_api (P1-02): the versioned host integration surface, twelve
  capability modules re-exporting the 51 symbols a host legitimately
  consumes, HOST_API_VERSION 1.0, two stability levels (every module stable
  except control, provisional), frozen both ways by a 65-test contract file
  and documented in VERSIONING.md.
- The beta contract manifest (BETA-02): a deterministic golden covering full
  signatures, dataclass fields, canonical defaults and enum members for the
  facade and all host_api symbols, environment-independent (proven identical
  across Python 3.11/3.12 and pydantic 2.8/2.13), with a CI test failing on
  any modification and a deliberate regeneration script.
- A multi-instance isolation guarantee (BETA-03): engines in one process are
  isolated by construction, tested (per-instance tool surfaces, interleaved
  runs, threaded one-engine-per-worker hosting), with the lifecycle doctrine
  in the README quick start and a new hosting example
  (09_multi_engine_hosting.py).

### Removed

- run_multi (BETA-03): the facade, runtime, internals, its test, the batch
  example and its documentation mentions. The documented lifecycle is one
  engine, one governed run at a time; parallelism belongs to the host.
- CERTIFIED_RUNTIME (BETA-02): removed from the certification enum; it had
  never been produced by any code path, and a contract must not carry an
  unattainable level. VERSIONING.md records the removal.

### Fixed

- M10 is rewritten as the planned empirical validation protocol it actually
  is (BETA-04): metrics and pass criteria preserved, every unbacked observed
  result removed, corrupted fragments repaired, execution and publication
  requirements stated. M9, M2 and the architecture mapping now source the
  projection properties to the offline Phase A fixture corpus and state that
  runtime does not assess noise or mode stability; the stale M2 link and the
  two broken M1 links are fixed (P2-01), replay documentation uses the real
  replay_verified/replay_recomposed API (DOC-02), the reachability ratchet
  documents that it measures reference, not runtime integration (P2-04), the
  concatenated .gitignore line is split (P2-02), the stale PyPI-is-planned
  README line is corrected, the examples README shows the real quickstart
  output, and the em-dashes are purged from the package, tests and README.


## [0.1.0a13] - 2026-07-23

The beta readiness campaign, closing an internal audit and an external one. It
changes what the package ships, what it claims, how it is published, and, in
three bounded places, what the kernel accepts. Those three are called out under
Security and Changed: each closes a gap where the runtime was more permissive
than it stated.

Upgrading from 0.1.0a12: no public API is removed. Two effect-path behaviours
become stricter and may surface an integration that was relying on the looser
one, which is the point of the change rather than a side effect.

### Removed

- Removed 52 unreachable modules, about 1600 lines that travelled in the wheel
  while nothing imported them. Twelve were the orphans reported by the a11
  audit; the rest surfaced from a reachability fixed point, and included three
  subsystems that had never been wired: the lexicon registry with its finance,
  legal and security vocabularies, the realization service and its templates,
  and the reflexive timeline insight and rendering layers. Those three sat on
  the wrong side of the open-core boundary: naming what a formal notice is, or
  rendering a timeline for a human, is realization, not kernel. The kernel keeps
  the contracts (lexicon entries and snapshots) and everything that constrains
  or introspects. Deletion history is in git if a design is ever revived.
- Removed the empty packages left behind, and the modules that died in cascade
  behind the ones removed.

### Added

- `tests/contracts/test_module_reachability_ratchet.py`: a module that nothing
  imports now fails the suite when it is introduced, rather than at the next
  audit. It resolves absolute, relative and dynamic imports, and treats a module
  reached only by its tests as alive.
- `tests/kernel/projection/test_unassessed_projection_axes.py`: pins that the
  projection certificate never attests an axis it did not measure.

### Changed

- `ProjectionValidator` no longer certifies unassessed axes. Noise robustness
  had no estimator and reused domain validity as a proxy; mode stability was a
  bare `True`. Both fed the certification level, so a LOCAL certificate attested
  six properties of which two were never evaluated. They are now recorded as
  unassessed in `checks_detail` and excluded from the level. Behaviour is
  unchanged: both hold whenever the domain does, which is the only branch that
  reaches the level computation. Implementing a real noise estimator remains
  open; what changed is the claim, not the estimator.
- `ProjectionCertificate` states its contract: a flag reports what the producing
  validator concluded, qualified by the `<axis>_assessed` markers.
- `ARVIS_LINGUISTIC_SPEC_V1.md` describes what the kernel actually ships. It
  named removed modules as architecture components, so the public specification
  described code that did not exist.
- Translated the remaining French comments and docstrings: the repository rule
  is English throughout, and sixteen files were breaking it.

### Security

- Hardened the release workflow. It now runs under `contents: read`, grants
  `id-token: write` to the publish job alone, accepts version tags only, and
  refuses to publish unless the tag names the packaged version and the changelog
  documents it. The full quality gate, the packaging checks and a clean-env
  install run before publication, and the published artifact is the one that was
  verified, passed between jobs rather than rebuilt.

## [0.1.0a12] - 2026-07-20

Version bump and the first publication path. No kernel logic changes.

### Added

- OIDC Trusted Publishing workflow for PyPI releases
  (`.github/workflows/release.yml`).

### Changed

- Bumped the package version from `0.1.0a11` to `0.1.0a12`.

> **Pre-history notice.** The entries from `0.1.0a1` through `0.1.0a11`
> below predate this repository's git history (first commit: 2026-07-23)
> and were never published: no git tag and no PyPI artifact corresponds
> to them. They are kept as the project's working journal from before
> publication, and cannot be independently verified against a released
> artifact. Verifiable history starts at `0.1.0a12` (first PyPI release,
> 2026-07-20) and `0.1.0a13` (first git tag).

## [0.1.0a11] - 2026-07-19

Campaign 8 seals the complete effect-selection context. A capability is now
bound not only to its frozen payload and authorization, but also to the exact
principal, tenant, authentication provenance, service/session and runtime
identity under which it was minted. The campaign also closes enum/scalar
canonical collisions and removes residual test-only production surfaces.

### Security

- Introduced immutable `AuthorizedEffectContext` material and removed the raw
  pipeline context from `ToolInvocation`, validation and legacy execution
  payloads. Invocation, capability and intent now commit the exact principal,
  tenant, authentication provenance, service/session and runtime bindings.
- `SyscallHandler` compares the current trusted identity with the sealed effect
  context before intent creation. Divergence revokes the capability, releases
  confirmation and produces no receipt or effect; `KERNEL_PRINCIPAL` is
  excluded from user tool effects. The final audit also pins the optional host
  binding commitment in this equality check.
- Canonicalization v3 dispatches `Enum`, `StrEnum`, `IntEnum`, `Flag` and
  `IntFlag` before scalar parents and preserves enum mapping-key identity.
  Redaction policy v5, commitment v5 and confirmation format v4 invalidate old
  hashes and confirmations explicitly.
- Removed production-packaged test effect routes and replaced security-sensitive
  runtime assertions with explicit fail-closed checks, including under
  optimized Python.
- Pinned Bandit in the development gate, wired the same security command into
  CI, and added a wheel-content check that rejects OS metadata, bytecode,
  caches and packaged test helpers.

### Host integration

- Defined the ARVIS/Veramem boundary: ARVIS owns frozen effect material,
  authorization capabilities, intent/receipt validation, result binding and
  commitments. Veramem owns real authentication and tenant resolution,
  PostgreSQL persistence, persistent confirmation/idempotency coordination,
  business service injection and distributed workers.
- Tool dependencies must be constructor-injected. Mutable runtime context,
  credentials, database sessions and live clients are forbidden effect-context
  material.

## [0.1.0a10] - 2026-07-19

Campaign 7 hardens the complete external-effect transaction. The campaign began
with eight adversarial reproductions against `0.1.0a9`: capability mint
forgery, payload mutation after authorization, forged authorization wrappers,
capability reuse after outbox failure, leaked confirmation reservations, run-ID
prefix collisions, unstamped production principals and in-memory sinks accepted
as durable. Every reproduction is now a normal passing regression test.

### Security

- **Canonical frozen effect payload.** Authorization creates one deeply isolated,
  immutable `FrozenEffectPayload`. Confirmation, schema validation, policy,
  idempotency, intent commitment and execution all use that same canonical
  object. Mutation of caller-owned containers after authorization cannot change
  the dispatched effect.
- **Registered non-forgeable capabilities.** `AuthorizedInvocation` no longer
  transports a mint secret. Each nonce is registered against an exact commitment
  covering invocation, authorization snapshot, confirmation and idempotency
  material. Unknown, cloned, modified, foreign, revoked or consumed capabilities
  are refused atomically.
- **Strict authorization outcome.** `ToolAuthorizationOutcome` is frozen and
  accepts exactly one typed path: a manager-owned capability or a typed refusal
  with its own denial snapshot. Generic wrappers, repaired snapshots and duck
  typing are rejected before intent creation.
- **Receipt-activated transaction.** Authorization produces only a `MINTED`
  capability. `SyscallHandler` records the exact intent, validates the sink
  receipt and only then activates the capability. Sink failure, invalid receipt,
  durable-position replay or activation failure revokes the capability and
  prevents direct fallback execution.
- **Exception-safe confirmation lifecycle.** Confirmation reservation uses an
  explicit transaction. Every provable pre-effect refusal or exception releases
  the reservation; started, completed, failed or uncertain effects consume it
  conservatively. A forged capability cannot release another capability's
  reservation.
- **Authenticated production identity.** Production effects require a host-stamped
  `AuthenticatedPrincipal` matching the turn owner (or the reserved kernel
  principal). Authentication source, strength, service and session hash are
  committed into the effect material.
- **Qualified durable sink.** Production requires an `AuditSinkManifest` declaring
  a database or distributed-log sink that is transactional and append-only.
  `InMemoryAuditSink` is explicitly classified as memory and refused in that
  posture. Receipt store identity and durable positions are checked fail-closed.
- **Complete causal identity and effective idempotence.** Causal IDs now contain
  the complete run ID rather than a 48-bit prefix. The deterministic
  `idempotency_key` is committed into the intent, persisted in the outbox, bound
  by the receipt through `intent_sha256`, exposed to structured and legacy tool
  adapters and stable across retries.
- **No direct production effect route.** Public manager and executor methods can
  no longer mint, activate or dispatch a capability. One `SyscallHandler` claims
  the private effect boundary exactly once; the supported effect path is syscall
  mediated and outbox backed.

### Architecture

- Extracted `ToolAuthorizationService` for immutable request preparation and
  policy material.
- Extracted `IntentOutboxService` for intent construction, receipt validation,
  durable-position replay protection and local publication.
- Extracted `EffectDispatcher` for single-use capability consumption and explicit
  effect-boundary classification.
- Shared fail-closed tool schema validation lives in `arvis.tools.tool_schema`.
- `SyscallHandler.handle`, `_record_intent`, `ToolManager.authorize`,
  `ToolExecutor._execute_invocation` and `tool_execute` are now orchestration
  entrypoints guarded by maintainability ratchet tests.
- Added the normative governed-effect architecture note and updated tool
  lifecycle, runtime concurrency doctrine and architecture invariants.

### Breaking changes and host migration

- Re-pin Veramem and other hosts to `0.1.0a10`; capability, activation and intent
  commitments changed during the campaign.
- Do not call `ToolManager.run`, `execute_authorized`, `activate_authorized`,
  `ToolExecutor.execute_invocation` or `ToolExecutor.execute`; use `CognitiveOS`
  or the governed `SyscallHandler` path.
- Production effect contexts must use `AuthenticatedPrincipal`.
- Production sinks must expose a qualifying `AuditSinkManifest` and return an
  `AuditReceipt` with the exact complete `run_id`, `causal_id`, intent hash and
  matching store fingerprint.
- Persist the complete intent, including `idempotency_key`, and forward that key
  to the external system. Ensure causal-ID storage is not sized for the former
  twelve-character run prefix.
- Keep one ARVIS runtime instance per request/turn. Capability and confirmation
  registries are thread-safe within one process but are not distributed across
  workers.

## [0.1.0a9] - 2026-07-18

Campaign 6: external-audit remediation. An external audit of 0.1.0a8
(consolidated 9.3/10) left four thresholds open on the effect path:
the pre-effect intent was recorded before the business authorization
existed, results were not cryptographically bound to their intents,
the canonicalization domain was not fully injective, and the execution
capability was publicly mintable and reusable. This release closes all
four, plus the confirmation, durability, run-identity and hygiene
findings, each pinned with its reproduced attack vector in
`tests/adversarial/test_campaign_audit_regression_2.py`.

### Security

- **P0: authorization before intent (Lot 1, a8 section 8).** The full
  business authorization (extraction, tool lookup, input schema,
  principal/tenant, confirmation reservation, ToolPolicy) now runs
  BEFORE the `tool.execute` syscall is issued
  (`ToolManager.authorize`); the verdict travels sealed on the minted
  `AuthorizedInvocation`; the pre-effect intent binds that exact
  verdict; the mutable `ctx.extra["tool_authorization_snapshot"]`
  channel is removed and a bare `tool.execute` without an
  authorization outcome is refused fail-closed. Every retry attempt is
  re-authorized, so a stale snapshot is unreachable by construction.
- **P0: result bound to its exact intent (Lot 2, a8 section 9).**
  Every journaled effect result carries the engagement digest of ITS
  intent (`intent_commitment_sha256`, stamped single-use by the
  handler); the bijection verifies the full tuple and refuses any
  permutation of same-syscall results; the journal digest (v2) binds
  ordered per-pair commitments, so a permutation changes the digest
  even though causal ids are envelope-stripped.
- **P0/P1: injective canonicalization domain closed (Lot 0, a8
  section 7).** Canonicalization v2: `bytearray` gets its own tag,
  path types and class identities are module-qualified, non-finite
  floats are refused, and underscore-prefixed private state is REFUSED
  rather than silently dropped (the explicit `__arvis_canonical__`
  serializer hook is the contract for private state). Downstream
  bumps: `REDACTION_POLICY_VERSION` 4, `COMMITMENT_VERSION` 4,
  `CONFIRMATION_FORMAT_VERSION` 3. No a8-era hash or confirmation is
  honoured. Property-based injectivity is enforced with Hypothesis.
- **P1: private, single-use capability (Lot 3, a8 section 10).
  BREAKING.** The minting authority is no longer a public attribute of
  `ToolExecutor`; the only handle is `claim_minting_authority()`,
  claimable exactly once (the `ToolManager` claims it at
  construction). Every capability carries a fresh nonce CONSUMED at
  execution: one authorization, one effect; a replayed capability is
  refused. `ToolExecutor` is removed from the `arvis.api` public
  exports.
- **P1: unique confirmation record commitment, mandatory TTL (Lot 4,
  a8 section 12).** Every issued confirmation computes
  `record_commitment = H(version, nonce, tool, payload_sha256,
  principal, tenant, issued_at, ttl, issuer)`; the proof binds THIS
  value, so two human decisions on the same effect never share a
  commitment. The TTL is mandatory and strictly positive (default
  300s); expired records are purged at reservation.
- **P1: durability proven, not declared (Lot 6, a8 section 14).
  BREAKING in durability-requiring profiles.** A durable sink now
  ANSWERS: `DurableAuditSink.append(intent)` returns an `AuditReceipt`
  binding exactly the persisted intent (engagement digest, run
  identity) and where it durably lives; the syscall boundary validates
  every receipt fail-closed. A bare callable sink is refused where
  durability is required; `InMemoryAuditSink` is the reference
  implementation. Exported on `arvis.api` for hosts.
- **Global run identity (Lot 5, a8 section 17).** A fresh unguessable
  `run_id` is generated at run entry, prefixes every causal id
  (global uniqueness across runs in a shared sink) and is journaled on
  every intent and result. It is ENVELOPE identity, stripped from the
  hashed material: the deterministic-commitment contract holds; the
  run <-> proof anchoring is the sink receipt's job. An accidental
  determinism (the raw artifact digest coinciding only through the id
  collision itself) is made intentional via the artifact's explicit
  canonical encoding.
- **Effect boundary classification (Lots 1/4, a8 constat 11).**
  `ToolResult.effect_boundary` distinguishes pre-effect refusals from
  crossed-boundary outcomes; a reserved confirmation is committed only
  when the boundary was crossed and released on any pre-effect refusal
  (schema violation, unknown tool, tool.validate refusal, policy
  denial): a human confirmation is never burned for an effect that
  never ran.

### Changed

- Invocation governance fields are filled (Lot 7, a8 section 13):
  `audit_required` travels from the tool spec; `consent_granted` comes
  from the trusted host composition channel `ctx.consent_granted`
  (host-stamped, string keys only, never request-facing extra);
  `idempotency_key` is derived deterministically and is stable across
  re-authorized retry attempts of the same logical action.
- The `assert` at the host declaration boundary is an explicit
  fail-closed raise (an assert vanishes under `python -O`; Bandit
  B101, a8 section 20).
- The engagement digest binds extracted effect parameters (tool name
  and payload, from the sealed invocation) instead of a lossy partial
  view of the runtime result object.

### Migration notes (hosts, veramem re-pin)

- `executor.authority` no longer exists; one `ToolManager` per
  executor; `from arvis.api import ToolExecutor` no longer resolves.
- A capability cannot be executed twice; syscall results carry
  `intent_commitment_sha256` and `run_id`.
- All commitments changed (canonicalization v2): any anchor stored
  under a8 is invalid; no a8 confirmation record is honoured.
- PRODUCTION-posture hosts must provide a `DurableAuditSink`
  (receipts), not a callable; the veramem realization is the
  PostgreSQL sink (chantier D4-e).
- `ToolConfirmation` gains `nonce`, `issued_at_unix`, `ttl_seconds`,
  `issuer` and `record_commitment`; `expires_at_monotonic` is no
  longer optional; `issue` refuses non-positive TTLs.


## [0.1.0a8] - 2026-07-17

Campaign 5: external-audit remediation. An external audit of 0.1.0a7
found a class of collision vulnerabilities in the effect-path
commitment machinery, plus gaps in confirmation lifecycle, journal
bijection, replay authentication and executor reachability. This
release closes them and moves the effect path from "high-level alpha"
toward an integrable kernel beta. Every reported P0 and P1 is closed
with a reproduced attack vector pinned as a regression test.

### Security

- **P0: injective canonicalization of effect material (Lot 0-1).** The
  a7 chain `deep_material -> _strip_volatile -> redact_for_commitment`
  reduced distinct business payloads to the same digest before
  SHA-256, so a confirmation granted to act on record-A could be
  consumed to act on record-B. A single injective encoder
  (`arvis.kernel_core.canonicalization`) now feeds every effect-path
  hash: type-preserving (`bytes`, `datetime`, `Decimal`, `UUID`,
  `Path`, `Enum`, sets, dataclasses each map distinctly), key-type
  preserving (`{1: x}` != `{"1": x}`), fail-closed on non-encodable
  values. `payload_commitment` and `effect_engagement_digest` are
  rebuilt on it; volatile stripping is confined to declared journal
  envelopes and never rewrites a business payload. A latent
  non-determinism (`process_id` in the engagement material) surfaced by
  the injective encoder is fixed by excluding runtime bindings
  explicitly. Bumps: `REDACTION_POLICY_VERSION` 2->3, `COMMITMENT_VERSION`
  2->3, `engagement_version` 1->2.

- **Generic host declaration channel (Lot 2).** New
  `arvis.kernel_core.host_declaration`: an opaque `host_context`
  (JSON-safe, canonicalized injectively) the host attaches to every
  governed intent, with `instance_label` as the one conventional key
  ARVIS reads (only to stamp boundary provenance on journaled intents,
  never in committed materials). Injected components may expose
  `governance_manifest()`, which `config_fingerprint` binds in full, so
  two differently configured components of the same class no longer
  share a fingerprint (audit constat 17).

- **P1-5: versioned, transactional confirmations (Lot 3).** Confirmation
  records carry an explicit `CONFIRMATION_FORMAT_VERSION` (starts at 2);
  a record of any other version is refused at reservation, so no a7-era
  confirmation is honoured. The lifecycle is two-phase
  `reserve -> commit / release`: the tool manager reserves before the
  policy, commits after the effect runs, and releases on a pre-effect
  denial, so a legitimate confirmation is never burned by a policy
  refusal and never double-spent. A `ToolAuthorizationSnapshot` (policy
  verdict, principal, tenant, risk, bound confirmation commitment) is
  bound into the effect engagement, so two identical effects authorized
  differently no longer share a commitment (audit constat 11).

- **P1-6: strict intent/result bijection (Lot 4).** New
  `arvis.kernel_core.syscalls.intent_result_bijection`: the commitment
  binds the journals only under an exact one-to-one correspondence.
  The a7 set-membership check missed duplicate intents, orphan results
  and syscall mismatches; the strict verifier requires exactly one
  intent and one result per causal id, agreeing on the syscall name,
  and fails closed as `audit_incomplete` on any deviation.

- **P1-7: authenticated replay (Lot 5).** BREAKING. The a7 `replay()`
  (optional expected commitment, so `replay_verified(ir)` accepted
  arbitrary fingerprints) is removed. `replay_verified(ir, *,
  expected_global_commitment)` makes the external anchor mandatory and
  authenticates the recomposed commitment against it;
  `replay_recomposed(ir)` recomposes without authenticating and is
  named for it. The expected commitment must come from a durable source
  outside the IR; the host owns that source's durability (documented
  host requirement).

- **P1-8: uncircumventable executor (Lot 6).** BREAKING. New opaque
  capability `AuthorizedInvocation`, minted only by the tool manager's
  `InvocationAuthority` after policy. `ToolExecutor.execute_invocation`
  runs a tool only from a verified capability; a bare invocation, a
  forged capability or one from another authority is refused. The
  `execute_authorized` rebuild-and-run bypass is removed, `execute()`
  forbids all direct execution, and `CognitiveOS.tool_executor` is no
  longer public. There is no path to an effect the policy did not
  authorize.

### Changed

- `CognitiveOS.replay(...)` removed; use `replay_verified(...)` (with a
  mandatory external commitment) or `replay_recomposed(...)`.
- `ToolExecutor.execute_authorized(...)` removed; tools run only through
  a manager-minted `AuthorizedInvocation`.
- `CognitiveOSConfig` gains `host_context`; `KernelServiceRegistry`
  gains `host_context` and `instance_label`.

## [0.1.0a7] - 2026-07-17

### Security

- **P0-2-a6: strict commitment_inputs validation.** The
  `commitment_inputs` block is validated fail-closed before any
  composition (`CommitmentInputs` frozen type,
  `validate_commitment_inputs`): exactly the four component keys, no
  extras, canonical lowercase sha256 hex values. A forged, incomplete
  or malformed block never composes into a formally valid commitment:
  it surfaces as an absent commitment with the dedicated reason
  `commitment_inputs_invalid`, refused under REQUIRED and flagged under
  DEGRADED. The permissive `.get(key)` composition is gone, and the
  exported block is the canonical validated form.

### Fixed

- **P0-4-a6: kernel-internal syscalls are functionally reachable.**
  `process.spawn`, `process.suspend`, `process.resume` and
  `interrupt.emit` now accept the uniform boundary contract
  (`ctx=None`, `causal_id=None`): the kernel principal on the trusted
  context channel reaches them, the intent outbox pairs with their
  results, and anything else stays denied. They were governed
  structurally but unreachable (denied without ctx, invalid-args with
  ctx). End-to-end tests now exercise the REAL registered syscalls with
  runtime objects, not probes (campaign-3 lesson applied).
- **P1-13-a6: normalized authorization boundary.** An exception raised
  by an access resolver or by the authorization policy no longer leaks
  through the syscall boundary: it is normalized into a journaled,
  fail-closed refusal with the stable reason code
  `authorization_failure`.

### Added

- **P0-3-a6: pre-effect engagement of exact parameters.** The intent
  outbox entry now carries `commitment_sha256`, computed BEFORE the
  effect runs: it binds the syscall, its materialized redacted
  arguments (`deep_material` walks object attributes so distinct
  payloads never collapse into a type marker), the principal, the
  tenant, the turn owner and the authorization outcome. Two effects
  with different parameters and identical results yield different
  composed commitments. Redaction policy bumps to v2 (tool and LLM
  payload fields covered: `tool_payload`, `arguments`, `messages`,
  `input_data`); the redaction primitives move to the kernel boundary
  (`arvis/kernel_core/syscalls/engagement.py`, re-exported unchanged
  from `arvis.api.commitment`). Commitment VALUES change (policy
  version is part of the hashed material). This closes the deferral
  documented at campaign-3 Lot 5.
- **Deterministic LLM prompt rendering (surfaced by the engagement
  digest).** The intent-enrichment prompt embedded a dataclass repr
  carrying `decided_at` (wall clock), making the LLM request, hence the
  pre-effect engagement, non-deterministic across identical runs. The
  prompt now renders the intent through an explicit deterministic
  projection excluding wall-clock fields; the `run_ir == to_ir`
  contract and cross-run commitment determinism hold again.
- **P0-1-a6: mandatory post-effect audit and intent/result bijection.**
  On the effect path the result journal is no longer best-effort: a
  journaling failure after an effect marks the execution
  AUDIT_INCOMPLETE (the effect happened; arvis refuses to pretend it
  proved it, never denies it retroactively). The intent/result
  bijection is verified where the journals are read
  (`_build_commitment_inputs`, decision D4-c): an effect intent without
  its paired journaled result, or the handler incompleteness flag,
  yields no commitment with the dedicated reason `audit_incomplete`;
  REQUIRED refuses the public result through the existing absence
  machinery (decision D4-b), DEGRADED flags it, and the view exposes
  `audit_incomplete`. The audit scenario (effect executed, journal
  down, REQUIRED commitment still produced) is closed and pinned by
  tests.
- **P1-5-a6: single invocation object from authorization to the tool.**
  The executor's canonical entry is now
  `execute_invocation(invocation, result, ctx)`: it receives the SAME
  `ToolInvocation` the policy evaluated, so user, principal, tenant,
  real turn risk, consent, audit and idempotency fields travel to the
  tool without reconstruction. `execute_authorized` remains as a
  deprecated compatibility path that rebuilds a minimal invocation and
  delegates. The direct-execution prohibition is unchanged.
- **P1-10-a6: bound, satisfiable tool confirmation (full object,
  decision D4-d).** New `arvis/tools/confirmation.py`:
  `ToolConfirmation` (frozen) binds a confirmation to the tool, the
  redacted payload hash, the principal, the tenant and a monotonic
  expiry; `ConfirmationRegistry` issues and consumes them with strict
  semantics (exact match on every binding, single use, expired records
  purged, a mismatch does NOT burn the record). `ToolInvocation` gains
  `confirmed`, `confirmation_id` and `confirmation_commitment`; the
  manager resolves the confirmation from the trusted composition
  channel (`ctx.confirmation_result`) against the registry, and the
  policy accepts a `requires_confirmation` spec only for a confirmed
  invocation. A tool declaring `requires_confirmation=True` was
  previously refused unconditionally; the host wires a registry through
  `CognitiveOSConfig.confirmation_registry`.
- **D4-e (P1-a6): effectful production requires a durable sink.** In
  the production profile, the first EFFECT syscall with no
  `audit_intent_sink` configured is refused at the point of use
  (reason `durable_sink_required`), before the intent is recorded and
  before the effect runs. A production profile without effects stays
  valid without a sink; local profiles never require one.

## [0.1.0a6] - 2026-07-17

### Fixed

- **Replay reproduces the governing postures.** The runtime profile
  that governed a run ("local", "production") is now recorded in
  `CognitiveContextIR.runtime_mode`, and the replay context builder
  reapplies the derived postures (global stability action, switching
  envelope, input-risk harden-only) from the record through a single
  shared helper (`apply_runtime_postures`), never from the replayer's
  environment (decision D-a extended to postures). Before this fix a
  production run whose verdict depended on a posture replayed with the
  permissive defaults and failed commitment verification. IR shape
  gains one context field; IR hash values change accordingly.

### Security

- **F-001-a5: a caller-declared risk never relaxes the verdict on a
  mixed payload.** The pure-scalar precondition of the input-risk policy
  is now coded (`is_pure_risk_payload`): the grading path (which may
  relax a sparse-projection artifact) is active only for a payload
  exclusively dedicated to the risk scalar (`{"risk": x}`). Any mixed
  payload is harden-only: the declared risk composes through
  `max_strictness`, the hardening is traced (`input_risk_harden`), and
  existing reasons are never superseded. The production profile sets the
  `harden_only` posture (`ctx.input_risk_mode`), so in production a
  declared risk never relaxes at all, pure payload included; unknown
  posture values fail closed to harden-only. Examples 02/04/09 moved to
  pure risk payloads; example 06 now demonstrates the harden-only
  doctrine on a real trade payload.

### Changed

- **F-002/F-003/F-004-a5: unified production invariants.** The
  PRODUCTION invariants now live in `CognitiveOSConfig.__post_init__`
  as the single source of truth: `audit_commitment_policy=REQUIRED` and
  no `runtime_controls`, whatever the constructor. A direct
  `CognitiveOSConfig(runtime_mode="production")` with the DEGRADED
  default is refused at construction, and a `production()` override
  that relaxes an invariant is refused rather than silently clamped.
  `CognitiveOS.config` is now a read-only property backed by a private
  `_config`: the runtime governs under the configuration it was built
  with, for its whole lifetime.

### Added

- **F-009-a5: mandatory access resolver for effect syscalls (closes the
  deferred B6 guard).** `register_syscall` refuses an EFFECT
  registration without an access resolver at import time: an ungoverned
  effect capability is structurally unreachable. Reference resolvers
  (`arvis/kernel_core/access/resolvers.py`) express each class's real
  rule under the single owner-scoped policy: kernel-internal syscalls
  (`interrupt.emit`, `process.*`) are owned by the runtime itself
  (reserved `KERNEL_OWNER_ID`; only `KERNEL_PRINCIPAL` on the trusted
  context channel passes, identity is never read from syscall
  arguments); turn-scoped syscalls (`tool.execute`, `llm.generate`) are
  owned by the turn's user, a stamped foreign principal is denied, and
  a call without an identifiable owner is denied fail-closed.
- **F-010-a5: governance manifest and enriched registry fingerprint.**
  `ToolRegistry.manifest()` describes the registered surface completely
  for governance: identity (registry name, implementation qualname,
  declared spec name) and every governance-relevant spec field
  (schemas as canonical sha256 hashes, never in clear; execution
  semantics; policy flags; capability manifest fields). The registry
  `fingerprint()` is now the sha256 of the canonical JSON manifest,
  versioned (`MANIFEST_SCHEMA_VERSION`); a non-canonicalizable declared
  schema refuses pinning (fail-closed). Fingerprint VALUES change with
  this release: hosts pinning the old name+qualname digest must re-pin
  (veramem: the `tool_registry_frozen` log hash changes, no functional
  impact, the engine-side registry is empty).
- **F-006-a5: complete invocation context (skeleton).** `ToolInvocation`
  gains opaque `principal`, `tenant` and `consent_granted` fields (host
  semantics, same doctrine as capability grants). The tool manager
  threads identity from the trusted context channel only (a stamped
  `Principal`; never request-facing extra), the bare `user_id` for
  owner scoping, and `risk_score` as the real turn risk: hardening
  composition of the declared input risk and the assessed collapse
  risk. The dormant `max_risk` spec policy becomes live and
  conservative: 0.0 only when no signal exists.
- **F-008-a5: durable audit intent before effect (outbox).** For any
  EFFECT syscall, the handler journals a `syscall_intent` entry BEFORE
  the call: structural metadata only (syscall name, causal id, tick,
  process id; no payload material), appended to the ordered
  `ctx.extra["syscall_intents"]` channel (paired with the result
  journal through the shared causal id) and emitted as a runtime event.
  A host `audit_intent_sink` (new `CognitiveOSConfig` field) is called
  synchronously with a copy of the entry before the effect; ANY failure
  to record the intent refuses the syscall
  (`reason_code=audit_intent_failed`, fail-closed). An intent without a
  paired artifact afterwards signals a crash during the effect: bounded,
  visible uncertainty. Authorization runs before the outbox: a denied
  effect never reaches it. Known gap carried to the composed-commitment
  lot: the timeline the current global commitment hashes is empty on a
  standard run (runtime events never reach `ctx.timeline`), so the
  intent/result journals will enter the commitment explicitly there.
- **F-007/F-018-a5: composed v2 global commitment with redaction before
  hash.** `arvis/api/commitment.py`: the global commitment is now the
  canonical hash of explicit named components with the version embedded:
  cognitive `ir_hash`, `timeline_commitment`, the digest of the REDACTED
  syscall journals (intents and results; content-bearing fields replaced
  by sha256 markers under the versioned `REDACTION_POLICY_VERSION`, so
  the audit gap of an environment-blind commitment over an empty
  timeline is closed by the journals entering explicitly), the registry
  manifest `fingerprint()`, the effective configuration fingerprint
  (governance fields; injected objects by presence and type identity
  only) and the active policy tables fingerprint. Replay (decision
  D-a): the non-cognitive components ride in the exported IR as a
  `commitment_inputs` block outside the cognitively hashed sections
  (`run_ir` carries it too; `run_ir == to_ir` holds); a replay
  recomposes from the declared block, never from the replayer's
  environment, so identical replay yields an identical commitment and a
  divergent environment stays detectable by comparison. Commitment
  VALUES change with this release. A missing component set yields
  `commitment_reason=commitment_inputs_unavailable` under the existing
  absence machinery (REQUIRED refuses, DEGRADED flags).

## [0.1.0a5] - 2026-07-16

Consolidation release (campaign 2): closes the composition-scope
findings of the 0.1.0a4 external audit around one invariant: the
enforcement phase of the gate stack is monotone
(ALLOW < REQUIRE_CONFIRMATION < ABSTAIN), and every sanctioned
exception is provenance-checked, traced and bounded.

### Added

- **Canonical verdict order and provenance (F-001 completion)**.
  `arvis/math/lyapunov/verdict_order.py` (strictness order,
  `max_strictness`, `is_relaxation`); provenance ledger and
  `enforce_monotone` guard in the gate trace helpers, wired around six
  enforcement gates; pipeline-level hypothesis property: the verdict
  transition trace never contains a relaxation outside the sanctioned,
  documented channels.
- **Versioned hard_block severity table (F-003)**
  (`arvis/math/stability/hard_block_policy.py`): stability reasons map
  to warning / confirmation / hard block; unknown reasons fail closed;
  the default table preserves the pre-A5 runtime behaviour and the
  applied table version is recorded in the trace.
- **Closed runtime mode set (F-008)** (`arvis/api/runtime_mode.py`,
  exported from `arvis.api` and the root): LOCAL, TEST, RESEARCH,
  PRODUCTION; unknown values are refused at configuration time.
- **Closed PRODUCTION profile (F-002, F-017, F-018, F-019)**.
  `CognitiveOSConfig.production()` fixes the mode and defaults the
  audit commitment policy to REQUIRED; production forces
  `global_stability_action="confirm"` and
  `switching_envelope_mode="enforce"` on every context, denies a tool
  declaring `required_consent` or `data_egress` when the matching gate
  is missing (config gains `consent_gate` / `egress_gate`), and
  freezes the tool registry automatically at the first run.
- **Tool effect governance (F-014, F-016, F-020)**. `timeout_seconds`
  is now a deadline on result acceptance (late result rejected with
  `ToolTimeoutError`; the effect may still have happened, interruption
  is a later chantier); automatic retry requires declared idempotence
  (a side-effectful, non-idempotent effect is never replayed, a
  missing spec means no automatic retry); declared input schemas are
  validated before the call and output schemas after it, each with its
  specific failure status, surfacing structural paths only (ZK).
- **Version coherence guard** (`tests/api/test_version_coherence.py`):
  the README Versioning table and the source-checkout fallback must
  equal `pyproject.toml`. **Runtime lifecycle contract**
  (`docs/architecture/RUNTIME_LIFECYCLE.md`): instance-per-request,
  unbounded reused-instance state (documentation side of F-022/F-023).

### Changed

- **Global stability policy is monotone (doctrine amendment)**. Under
  `action="confirm"`, global instability now hardens ALLOW to
  REQUIRE_CONFIRMATION (it previously did not), and the
  ABSTAIN -> REQUIRE_CONFIRMATION reinterpretation only applies to an
  ABSTAIN produced by the global stability axis itself (provenance
  checked, unknown provenance fails closed); a foreign veto
  (projection, kappa, memory, adaptive) is never relaxed. The
  campaign 1 doctrine of a blanket product transition is amended
  accordingly. The `gate_policy` confirm branch composes through
  `max_strictness`.
- **Fail-closed composition (F-005)**: a fusion failure abstains
  instead of falling back to the pre-fusion verdict; an unavailable
  validity envelope abstains; the input-risk gate abstains on
  exception and only relaxes sparse-projection artifacts (F-006,
  provenance checked); the PI override trace records applied
  transitions only.
- **Switching safety is honest (F-004)**: the hardcoded
  `effective_switching_safe = True` is replaced by a
  `switching_envelope_mode` knob ("soft" by default, unknown modes
  fail closed into enforcement; production sets "enforce").
- **Runtime configuration (F-007, F-009, F-012)**: `CognitiveOSConfig`
  is frozen; `force_tool` only selects a tool and execution requires
  an explicit `force_execution=True` (retries keep executing);
  `audit_commitment_policy=REQUIRED` with `enable_trace=False` is
  refused.
- **One registry**: the runtime and its `ToolManager` now govern the
  registry the host registered tools on (the runtime previously built
  its own empty registry and evaluated the tool policy against it).
- **Reproducible gate tooling**: `ruff==0.14.3`, `mypy==1.19.1`,
  `pytest==8.4.2` pinned in the dev extras (plugins stay unpinned
  until the dev lockfile lands); `types-jsonschema` added for the new
  runtime `jsonschema` use.

### Deferred

- Execution commitment chain (F-010, F-011, F-013, F-021, F-032):
  campaign 3, targeted at 0.1.0a6.
- LLM runtime governance (F-024 to F-031): dedicated campaign.

## [0.1.0a4] - 2026-07-16

Hardening release: the seven kernel-scope findings of the external
audit (F-001, F-002, F-004, F-009, F-010, F-013, F-015) plus the end
of the A2 context decomposition. One principle ties the safety lots
together: a failing guarantee mechanism can never relax.

### Added

- **TrustedRuntimeControls (F-001)**
  (`arvis/api/runtime_controls.py`, root export). Host-only controls
  (`force_tool`, `force_execution`, `force_safe_projection`,
  `force_safe_switching`) are injected by composition through
  `CognitiveOSConfig.runtime_controls` and rejected in the production
  runtime profile. Abuse tests assert that injecting any of the four
  keys through the request-facing `extra` channel is inert and that an
  ABSTAIN verdict can never be relaxed by overrides.
- **Governed tool registry (F-004, kernel part)**. `ToolRegistry.register`
  refuses re-registering an existing name unless an explicit
  `replace=True` is passed; `freeze()` locks the registry after
  bootstrap (any further mutation refused, explicit replacement
  included) and returns a deterministic, order-independent sha256
  fingerprint of the tool surface; `freeze_tools()` exposed on
  `CognitiveOS` and `ArvisEngine` for host-side pinning.
- **AuditCommitmentPolicy (F-015)** (`arvis/api/audit.py`, root
  export). The absence of an audit commitment is never silent: every
  result view carries the applied policy, a reason code when the
  commitment is missing (`ir_not_serializable`, `timeline_not_journal`,
  `timeline_commitment_failure`, `commitment_hash_failure`) and an
  explicit degradation flag. REQUIRED refuses an unauditable run
  (`ArvisSecurityError`), DEGRADED (default) records the visible
  degradation, OPTIONAL records the reason only. Threaded through
  `CognitiveOSConfig.audit_commitment_policy` to both the run and
  replay paths.
- **Packaging contract for the IR schema (F-010)**.
  `arvis/api/schema/ir_schema.json` now ships in the wheel
  (package-data) and the sdist (MANIFEST.in); the CI build job asserts
  the schema inside the built wheel and reads it back from an
  installed wheel through `importlib.resources`; pytest locks the
  canonical resource access path and both packaging declarations.
- **Fail-closed gate contract tests**
  (`tests/kernel/stages/test_gate_fail_closed.py`), including
  hypothesis property tests of the monotone strictness invariant
  ALLOW < REQUIRE_CONFIRMATION < ABSTAIN on the enforcement gates.
- **Audit artifact mutation guard**
  (`tests/api/test_audit_structures_immutable.py`): recursive mutation
  of an exported IR can never diverge the view from its commitment;
  replay does not mutate its input.

### Changed

- **Gates are fail-closed (F-002)**. An exception inside a verdict
  gate (projection enforcement, kappa hard block, global stability
  policy, validity enforcement) now forces ABSTAIN with a traced
  verdict transition (`*_fail_closed`, reason `gate_exception`)
  instead of returning the upstream verdict; failing safety
  computations report unsafe (`global_safe=False`,
  `switching_safe=False`) instead of safe. The A1 error routing is
  unchanged; only the returned value hardens.
- **strict_mode has one coherent channel (F-009)**.
  `CognitiveOSConfig.strict_mode` is now wired through
  `CognitivePipeline` to the stability bootstrap and merged
  monotonically with the `ARVIS_STRICT_STABILITY` env var: either
  channel can enable the strict profile, neither can disable the
  other.
- **Audit artifacts are sealed at the commitment boundary (F-013)**.
  The stored IR of a result view is detached at hash time (rebuilt
  from the exact hashed bytes) so no upstream alias can diverge the
  payload from its hash, and `to_ir()` exports a defensive deep copy.
  Probe conclusion recorded: 69 frozen dataclasses carry mutable
  containers, but the reproducibility break happens through aliasing
  of the hashed artifact; mass container conversion deliberately
  avoided.
- **A2 complete (arvis-projection-v2)**. The seven projection legacy
  aliases on `CognitivePipelineContext` (`projection_certificate`,
  `projection_domain_valid`, `projection_margin`, `projected_state`,
  `pi_state`, `projection_view`, `projection_view_raw`) were removed
  after migrating every callsite (854 -> 792 lines): canonical writers
  write `ctx.projection.*` only, duck-typed readers adopt the
  projection-first dual pattern with a plain-attribute fallback for
  mock contexts, and the PI resolver now reads the canonical
  `ctx.projection.structured_projection` (it silently depended on the
  facade before). `FROZEN_FACADE_PROPERTIES` shrinks by exactly those
  seven names.
- `arvis/api/version.py`: the source-checkout `PACKAGE_VERSION`
  fallback, which had silently stayed at `0.1.0a2` since the a3 bump
  (an F-018 instance), now mirrors the package version again.

### Removed

- The request-facing `extra` channel for `force_tool`,
  `_force_execution`, `force_safe_projection` and
  `force_safe_switching` (F-001): no gate or runtime path reads these
  keys from `ctx.extra` anymore; replaying an old IR carrying them is
  inert by construction.
- The projection legacy alias block and its
  `TODO(arvis-projection-v2)` marker (A2).

### Notes / next

- veramem follow-ups once the pin is bumped: call
  `engine.freeze_tools()` at the end of backend bootstrap and log the
  fingerprint (ZK-safe scalar); evaluate
  `AuditCommitmentPolicy.REQUIRED` for the governed agent path (the
  effectful profile).

## [0.1.0a3] - 2026-07-15

### Added

- **Broad-except classification guard**
  (`tests/contracts/test_broad_except_guard.py`). Every broad handler in
  `arvis/` must now re-raise or build a typed error (C1), route through the
  sanctioned error machinery (C2: `ErrorManager` methods, `normalize_error`,
  the syscall failure helpers, `_attach_degraded`, the canonical boundary
  adapters of `arvis/errors/boundaries/`, `_attach_mid_trace_failure`), or
  carry a normalized `# arvis-broad: <reason>` justification marker (C3).
  The zone ratchet is closed at ceiling 0: no zone is exempt.
- **Context facade shrink ratchet**
  (`tests/contracts/test_context_facade_ratchet.py`). Freezes the 63
  compatibility properties of `CognitivePipelineContext`: new code must use
  the sub-contexts directly, and the facade can only shrink until the
  callsite migration tracked in-code as TODO(arvis-projection-v2).

### Changed

- 37 broad `except Exception` handlers narrowed to their actual failure
  contracts (numeric coercion triples/quadruples, `ImportError` on designed
  import fallbacks, `ValueError` on enum construction,
  `AttributeError`/`TypeError` on duck-typed assignment guards) across the
  api, adapters, ir, telemetry, math, stability, conversation, runtime,
  cognition, kernel_core and kernel zones.
- Around 40 deliberate fail-soft boundaries now carry the machine-checkable
  `# arvis-broad:` marker (total coercion primitives, observe-only
  telemetry, defensive view enrichment, replay boundary, the global
  stability observer, the conversation bridges, hook isolation,
  per-rule/per-entry isolation, best-effort owner resolution).

### Removed

- Five dead compatibility aliases on `CognitivePipelineContext`
  (`control_runtime`, `quadratic_lyap_snapshot`, `runtime_projection`,
  `structured_projection`, `use_paper_slow_dynamics`), each verified to
  have zero attribute access and zero string/getattr access across arvis,
  tests and compliance (898 -> 854 lines).

## [0.1.0a2] - 2026-07-09

### Removed

- Unused kernel key-value memory substrate (`kernel_core/memory/*`, `memory.*`
  syscalls, observation-long journal). No consumer, and its plaintext record
  model was off-thesis relative to the ZKCS long-term declarative memory
  (`arvis/memory/*`), which remains the memory of arvis.
  
### Added

- **Packaging and typing.** Declared `[build-system]` (setuptools +
  `setuptools.build_meta`); ship a PEP 561 `py.typed` marker so downstream type
  checkers (starting with veramem) see arvis as a typed package; expose the
  top-level `arvis.__version__`, single-sourced from the installed package
  metadata; add a CI `build` job that produces the wheel and sdist, runs
  `twine check`, asserts `py.typed` is present in the wheel, and smoke-imports
  the built wheel in a clean virtual environment. First tag-consumable release.
- Capability manifest on `ToolSpec`: declarative governance metadata so a host
  can govern sovereignty, egress and consent uniformly across local and external
  (e.g. MCP) tools. New fields: `provider` (third-party identity), `data_egress`
  (outbound data flow), `data_class` (host-defined sensitivity),
  `required_consent` (opaque consent key) and `reversible` (undo-ability), plus
  the derived `crosses_trust_boundary` property. ARVIS does not interpret the
  opaque labels; the host maps them onto its consent system, data taxonomy and
  egress policy. Defaults preserve prior tool behavior. `examples/05_tool_authorization.py` extended
  to contrast a sovereign tool with a connected/egress one, and the tool docs
  (authoring guide, tool system spec) document the manifest.
- Governed input-risk gate: an explicit top-level `risk` scalar in the cognitive
  input is graded by a three-band policy (low -> ALLOW, medium ->
  REQUIRE_CONFIRMATION, high -> ABSTAIN). It supersedes the sparse-projection
  fail-closed for pure risk-scalar inputs while never relaxing a real safety
  veto (kappa / adaptive instability), and keeps the emitted IR consistent.

### Notes / next

- Unify the emitted IR version string (currently divergent across
  `arvis/api/ir.py` = `arvis-ir.v1`, `arvis/ir/version.py` = `1.0`,
  `arvis/adapters/ir/state_adapter.py` = `1.0`, and the `1.0.0` shown in
  `docs/IR.md` / `docs/ARVIS_STANDARD_V1.md`). Deferred to the IR-alignment
  track (P0.3).
- Minimal valid projection + differentiated gate (low -> ALLOW,
  medium -> REQUIRE_CONFIRMATION, high -> ABSTAIN) (P0.1 / P0.2).

## [0.1.0a1] - Unreleased

First coherence pass toward a public alpha. This release resolves versioning
and positioning inconsistencies; it does not add features.

### Changed

- **Versioning is now coherent across three explicit axes.** Package version
  `0.1.0a1`, API version `0.1`, standard version `draft-v1`.
- `pyproject.toml`: `version` set to `0.1.0a1`; classifier changed from
  `Development Status :: 4 - Beta` to `Development Status :: 3 - Alpha`.
- `arvis/api/version.py`: `API_VERSION` changed from `1.0.0` to `0.1` so the
  emitted public contract does not over-promise a stable API; the
  `PACKAGE_VERSION` source-checkout fallback now mirrors the package version
  (`0.1.0a1` instead of `0.0.0-dev`).
- `README.md`: repositioned as an honest `0.1.0-alpha` preview with a
  developer-first install path and a Known Limitations section; removed the
  "Beta" status.

### Added

- `arvis/api/version.py`: `STANDARD_VERSION` constant (`draft-v1`), exported
  from `arvis.api`.
- `CHANGELOG.md` (this file).

### Tests

- `tests/api/test_api_contract_v1.py`: version lock updated to
  `API_VERSION == "0.1"` (was `1.0.0`). The public API fingerprint is computed
  from the top-level `arvis.__all__` and is unaffected by this change.
