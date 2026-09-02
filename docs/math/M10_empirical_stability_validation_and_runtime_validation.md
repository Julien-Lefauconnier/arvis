# M10: Empirical Stability Validation Protocol and Campaign Report

> **Status: protocol executed on synthetic corpora; reports in
> sections 10 and 11.** Sections 1 to 9 are the registered protocol,
> unchanged. Campaign MATH-B (2026-09-01) executed it on the
> deterministic synthetic corpus $\mathcal{D}$ = D-1.0 with
> pre-registered thresholds; section 10 records the observed values,
> the judgment and the mechanism findings. Only the status pointers
> of sections 2, 5 and 9 were updated to reference section 10; no
> criterion of the registered protocol changed. **Scope of the empirical
> claim, precisely: the campaign validates the measurement harness
> and the kernel's decision mechanics under controlled synthetic
> dynamics. It is not evidence about production traffic**, and the
> certification level vocabulary of the runtime is still the only
> stability attestation ARVIS makes about deployed behavior. The
> offline Phase A of the projection layer remains documented in
> `M3_appendix_projection_validation.md`.

## 1. Objective

Define the empirical validation layer of the ARVIS Cognitive Operating
System: the dataset, the metrics, the pass criteria and the publication
requirements under which the theoretical results of M6–M9 would gain
runtime empirical support.

When executed, this protocol is intended to provide:
- quantitative confrontation of the theoretical results of M6–M9 with
  observed runtime behavior,
- runtime characterization of stability behavior,
- statistical assessment of robustness and practical stability claims,
- an evidence-backed description of the validity envelope under
  realistic conditions.

---

## 2. Position in the ARVIS Mathematical Stack

| Layer   | Nature                            | Status                       |
|---------|-----------------------------------|------------------------------|
| M0–M9   | Theoretical / structural          | Written, self-consistent     |
| M3 Phase A | Empirical, offline, projection layer | Executed (`tests/math/`) |
| M10     | Empirical, runtime, closed loop   | **Executed: D-1.0 (sec. 10), D-2.0 (sec. 11)** |

---

## 3. Validation Scope

All metrics of this protocol apply exclusively to trajectories that
remain inside the validated projection domain:

$$
\forall t, \quad o_t \in \mathcal{O}_{\text{valid}}
$$

as defined and bounded in M3.

### 3.1 System Under Test

The evaluated closed-loop pipeline is:

$$
o_t \ \xrightarrow{\Pi}\ (x_t,\ z_t,\ q_t,\ w_t)\ \to\ W_t\ \to\ \widehat{\kappa}_t\ \to\ v_t^{\text{gate}} \ \to\ v_t^{\text{final}} \ \to\ u_t
$$

with:

$$
v_t^{\text{final}} = \min_{\succ}(v_t^{\text{gate}},\ v_t^{\pi})
$$

including in particular:
- projection layer ($\Pi$)
- composite Lyapunov evaluation
- adaptive $\kappa$ estimator
- GateStage (verdict computation)
- PiBasedGate (projection-control layer $\Pi_{\text{ctrl}}$)
- control modulation layer

---

## 4. Validation Dataset (to be constructed)

### 4.1 Dataset Construction

A deterministic, reproducible validation corpus $\mathcal{D}$ will be
constructed, containing:
- nominal (healthy) trajectories
- boundary / edge-of-domain cases
- adversarial-style perturbations (bounded)
- high-frequency switching stress cases
- memory-intensive / long-horizon cases
- conflicting or inconsistent signal inputs

### 4.2 Dataset Requirements

$$
\mathcal{D} = \{ o_{0:T_i}^{(i)} \}_{i=1}^N
$$

with:
- bounded trajectory lengths $T_i$
- perfect reproducibility (fixed, published seeds; deterministic
  projection)
- intentional coverage of the projection domain corners and interior

The corpus, its seeds and its generator are versioned artifacts: the
campaign is not considered executed unless a third party can regenerate
$\mathcal{D}$ bit-for-bit and rerun every metric.

---

## 5. Metrics and Pass Criteria

Every subsection states the metric and the criterion the runtime has
to satisfy. The observed values are recorded in sections 10 and 11.

### 5.1 Lyapunov Evolution

**Metric**: $\Delta W_t = W_{t+1} - W_t$

**Evaluations**:
- full distribution of $\Delta W_t$
- proportions: $P(\Delta W_t < 0)$ (contraction),
  $P(\Delta W_t \approx 0)$ (marginal), $P(\Delta W_t > 0)$ (expansion)

**Pass criterion**: contraction events dominate; positive excursions
are bounded and rare, with the thresholds fixed and published before
the campaign runs.

### 5.2 ISS Residual Bound

**Metric**:
$W(t) - C e^{-\beta t} W(0)$ and the empirical gain
$\Gamma = \sup_t W(t) / \sup_{k \leq t} \|w_k\|$

**Pass criterion**:
- bounded empirical gain $\Gamma$
- no divergence on $\mathcal{O}_{\text{valid}}$
- a practical residual tube of the form
  $W(t) \leq \Gamma(\bar{w}) + r$ with published constants

### 5.3 Adaptive Stability Estimation

**Metric**: $\widehat{\kappa}_t$ (smoothed adaptive contraction
estimate)

**Evaluations**:
- distribution of $\widehat{\kappa}_t$
- regime frequencies (stable / marginal / unstable)
- adaptive margin $m_t = \widehat{\kappa}_t - \kappa_{\text{threshold}}$

**Pass criterion**: the stable regime dominates; the critical regime
is localized near domain boundaries; the unstable regime is rare and
transient, per pre-registered thresholds.

### 5.4 Kappa Violation Frequency

**Metric**: $P(\kappa^t < \kappa_{\text{threshold}})$

**Pass criteria**:
- violation frequency below a pre-registered bound
- violations associated with adversarial inputs, projection edge cases
  or switching boundary conditions
- **hard invariant of M6, checked on every violation**: whenever a
  violation occurs, the gate abstains:

$$
v_t^{\text{gate}} = \text{ABSTAIN} \Rightarrow v_t^{\text{final}} = \text{ABSTAIN}
$$

### 5.5 Gate Behavior Distribution

**Metric**:
$v_t^{\text{final}} \in \{\text{ALLOW}, \text{REQUIRE\_CONFIRMATION}, \text{ABSTAIN}\}$

**Evaluations**:
- marginal frequency of each verdict
- conditional probabilities $P(v_t \mid \Delta W_t, \widehat{\kappa}_t)$

**Pass criterion**: ALLOW dominates in the stable regime,
REQUIRE\_CONFIRMATION concentrates near marginal zones, ABSTAIN
concentrates in regions of detected instability: the gate behaves as a
monotone stability filter.

### 5.6 Projection-Control Overrides

**Metrics**:

$$
P(v_t^{\pi}), \qquad P(v_t^{\pi} \prec v_t^{\text{gate}}), \qquad P(v_t^{\text{final}} \prec v_t^{\text{gate}})
$$

**Purpose**:
- measure how often structural constraints dominate energy-based
  decisions
- quantify the contribution of $\Pi_{\text{ctrl}}$ in restricting
  unsafe transitions

### 5.7 Closed-Loop Feedback

**Invariant under test**:
$\Delta W_t > 0 \Longrightarrow u_t \downarrow$

**Pass criterion**: an increase in the Lyapunov value produces a
measurable decrease in aggressiveness ($\epsilon$) and exploration
scale, supporting the negative feedback loop claimed in M7.

### 5.8 Perturbation Decomposition

**Decomposition**:
$w_t = w_t^{\mathrm{proj}} + w_t^{\mathrm{noise}} + w_t^{\mathrm{switch}} + w_t^{\mathrm{adv}}$

**Pass criterion**: perturbation sources are identified and bounded;
no evidence of uncontrolled amplification.

### 5.9 Validity Envelope Compliance

**Metric**: $P(\mathcal{V}_t.\mathrm{valid})$ where $\mathcal{V}_t$ is
the runtime validity certificate.

**Pass criterion**: high compliance rate inside
$\mathcal{O}_{\mathrm{valid}}$, with every violation traced to a known
stress condition, supporting
$o_t \in \mathcal{O}_{\mathrm{valid}} \Longrightarrow \mathcal{V}_t.\mathrm{valid} = \mathrm{True}$.

---

## 6. Target Result Statement (hypothesis)

**T10 (to be established): Empirical Stability Validation**

Under:
- the validated projection domain (M3),
- bounded composite perturbations,
- the fully implemented GateStage and adaptive estimator (M4–M5),

the campaign would have to exhibit, on every tested trajectory:

$$
W(t) \leq C \, e^{-\beta t} \, W(0) + \Gamma_{\text{emp}}(\bar{w}) + r
$$

together with the structural filtering invariant:

$$
v_t^{\pi} = \text{ABSTAIN} \Rightarrow v_t^{\text{final}} = \text{ABSTAIN}
$$

and the monotone non-relaxation property of M11–M12:

$$
v_t^{\text{final}} \preceq v_t^{\text{gate}}
$$

T10 remains a hypothesis until the campaign runs and its artifacts are
published.

---

## 7. Theoretical Results Awaiting Runtime Evidence

| Result | Theoretical claim              | Runtime empirical status |
|--------|--------------------------------|--------------------------|
| T6     | Gate stability preservation    | pending (this protocol)  |
| T7     | Closed-loop adaptive stability | pending (this protocol)  |
| T8     | Robust practical stability + ISS | pending (this protocol) |
| T9     | Global validity envelope       | pending (this protocol)  |
| T11–T12 | Decision monotonicity and stability algebra | pending (this protocol) |

The offline Phase A evidence for the projection layer itself (bounded,
locally Lipschitz, noise-robust, switching-stable, Lyapunov-compatible
on the fixture corpus) exists and is documented in
`M3_appendix_projection_validation.md`.

---

## 8. What This Protocol Will Not Establish

Even fully executed, this campaign does not prove or claim:
- global stability outside $\mathcal{O}_{\text{valid}}$
- worst-case adversarial resilience (minimax sense)
- asymptotic convergence guarantees for **all** possible trajectories
- tightness of the residual tube constants

And as long as it is not executed, **no ARVIS release should be read as
certifying runtime stability behavior beyond what `VERSIONING.md`
states**: the projection certificate's noise robustness and mode
stability axes are not assessed, and `noise_gain_estimate` is always
`None`.

---

## 9. Execution and Publication Requirements

The campaign is considered executed only when, together:

1. the corpus $\mathcal{D}$, its generator and its seeds are published
   as versioned artifacts;
2. every metric of section 5 has an observed value with its
   pre-registered threshold;
3. the full run is reproducible bit-for-bit by a third party;
4. the results are recorded in this document (turning it from protocol
   to report) with a changelog entry.

These four conditions were met by campaign MATH-B; section 10 is the
record. The certification level vocabulary of the runtime
(`VERSIONING.md`, certification levels) remains the only stability
attestation ARVIS makes about deployed behavior.

---

## 10. Campaign Report: MATH-B, 2026-09-01

### 10.1 Identity and registration

- Corpus: $\mathcal{D}$ = **D-1.0**, master seed 20260901, 7 families
  (nominal, boundary, adversarial, switching_stress, long_horizon,
  conflicting, declared_risk), 56 trajectories, 1440 turns. Generator,
  seeds and manifest published under `validation/m10/`
  (`corpus_manifest.json`); the corpus is bit-for-bit reproducible
  (pinned by `tests/math/m10/`).
- Thresholds: 12 criteria proposed, then **registered unmodified by
  the project owner on 2026-09-01, before any full-corpus run**
  (`validation/m10/thresholds.py`, decision DM-B2).
- Harness: closed-loop, pipeline level. Each turn runs a real
  `CognitivePipeline`; the harness threads the scientific state, the
  fast and slow Lyapunov states, the switching runtime and the
  adaptive observer across turns (the host role). The declared_risk
  family deliberately runs unthreaded. No LLM anywhere; fully
  deterministic; runs in seconds.
- Reproduction: `python -m validation.m10 run` then
  `python -m validation.m10 sweep` (Python 3.11+, no network). The
  per-turn measurements (3 MB) regenerate identically rather than
  being tracked.

### 10.2 Judgment against the registered thresholds

**11 of 12 criteria passed.** Per the registration discipline, the
failure is reported as a failure and the thresholds were not revised
after observation.

| Criterion (section) | Registered | Observed | Verdict |
|---|---|---|---|
| 5.1 nominal contraction dominates | >= 0.60 | 0.516 | **FAIL** |
| 5.1 bounded expansion | <= 1.50 | 0.563 | pass |
| 5.2 no divergent trajectory | == 0 | 0 | pass |
| 5.2 bounded energy sup W | <= 6.0 | 1.496 | pass |
| 5.3 estimator availability | >= 0.50 | 0.833 | pass |
| 5.4 ABSTAIN never relaxed (M6) | == 0 | 0 | pass |
| 5.5 adversarial ALLOW share | <= 0 | 0.0 | pass |
| 5.5 ALLOW given expansion | <= 0.05 | 0.0 | pass |
| 5.6 override data present | >= 1 | 1440 | pass |
| 5.7 negative feedback consistency | >= 0.95 | 1.00 | pass |
| 5.8 bounded projection component | <= 10.0 | 0.0 | pass |
| 5.9 envelope alive in domain | >= 0.10 | 0.176 | pass |

The failed criterion is substantive and instructive: on the nominal
family the observation axes follow a bounded exogenous walk, and the
composite energy the gate consumes tracks them. Nothing in the
closed loop pulls the corpus's observations toward equilibrium (the
loop adjusts verdicts, not the synthetic inputs), so contraction
events sit near one half (0.516) instead of dominating. The
criterion, as registered, measured a property of the corpus's
dynamics rather than of the kernel. It stays failed on D-1.0; a
future corpus revision should encode the intended contraction regime
in the input dynamics (state-feedback synthetic inputs), and the
lesson is recorded here rather than papered over.

Disclosed instrument correction: run 1's distribution encoder
omitted verdicts with zero share, so the two zero-observation
criteria of 5.5 resolved to missing data and scored FAIL under the
fail-closed judge even though the observed ALLOW mass was exactly
zero in both. The encoder now emits every canonical verdict with an
explicit share; the registered thresholds were untouched, and run
1's judgment is preserved as
`validation/m10/artifacts/judgment_run1_encoder_defect.json`.

### 10.3 Verdict distribution observed on D-1.0

Overall: ABSTAIN 85.6%, REQUIRE_CONFIRMATION 14.4%, **ALLOW 0.0%**
(0 of 1440 turns). The refusal-shaped criteria pass trivially in
such a regime, which is why the mechanism findings of 10.5 matter
more than the marginals: the corpus exercises the fail-closed side
of the gate far more than its permissive side.

The declared_risk family shows the graded input-risk ladder with
zero bleed between bands: declared risk in the allow band produced
REQUIRE_CONFIRMATION on 59/59 turns, the confirm band
REQUIRE_CONFIRMATION on 76/76, the block band ABSTAIN on 57/57.
Monotone, deterministic, no crossovers. The ALLOW rung itself is
unreachable on this corpus: the pre-verdict floor is already
REQUIRE_CONFIRMATION on a cold pipeline (`switching_unsafe_monitoring`,
`projection_boundary`), and the low-band relaxation is then refused
by the provenance guard (`input_risk_relax_denied`,
`verdict_provenance_not_artifact`). Both are fail-closed guards
working as specified; the graded ladder is effectively two-level on
synthetic turns.

### 10.4 Measured constants (LOT B2, report-only per DM-B1)

M13 flags the constants of assumption A12 as assumed, not measured.
This campaign measured both on D-1.0; per decision DM-B1 the values
are published here and in `constants.json` and **no runtime default
changes** (calibration on real traffic remains reserved, decision
DM4).

- Contraction factor $\alpha$ (nominal family, per-step
  $1 - W_{t+1}/W_t$ over 99 contracting pairs): median 0.348,
  p10 0.091, p90 0.622; contraction share of steps 0.538.
- Target-map Lipschitz constant $L_T$ (4000 sampled ratios over an
  explicit, published input metric on symbolic states): median
  0.126, p99 0.360, max 0.736, against the assumed 1.0.
- Small-gain margin $\kappa_{eff} = \alpha - \gamma_z \eta L_T$:
  assumed 0.13; at the conservative quantiles (alpha at p10, L_T at
  p99) the measured value is **0.084 > 0**. The small-gain condition
  survives measurement on D-1.0 with a reduced but positive margin.
  Caveats: alpha is conditioned on contracting steps of a synthetic
  family; L_T depends on the declared input metric; neither is a
  production estimate.

### 10.5 Mechanism findings

1. **The adaptive layer was structurally dead and is now live
   (DM-B0).** The MATH-A rename split the estimator snapshot into
   `kappa_raw/kappa_clipped/kappa_smoothed`; the runtime observer
   kept reading the historical `kappa_eff` field through a silent
   `getattr`, so the whole layer (kappa bands, confirmation forcing,
   ABSTAIN veto, recovery-relaxation block) never fired on a live
   path. Fixed RED-first during this campaign, direction verified
   strictly hardening on every consumer. No previously green test
   moved, which quantifies how far the live conditions were from the
   suite's reach; the m10 harness now pins layer liveness.
2. **Once live, the adaptive hard veto dominates non-contracting
   dynamics.** With margins $\ln(J)/\tau_d + \ln(1-\kappa)$ mostly
   positive on a corpus whose energy does not contract (mean margin
   +0.137; bands: hard 1107, critical 51, warning 16, stable 26 of
   1200 available turns), the final verdict source is the hard
   adaptive veto on 952 of 1248 threaded turns. This is the
   fail-closed reading of A12 doing exactly what it says under
   sustained non-contraction; on real, partly contracting traffic
   the band mix is an open measurement (DM4).
3. **Cold-start evidence, quantified.** An unthreaded turn faces an
   evidence-free PAC ceiling: risk_ucb = 1.0 on all 192 unthreaded
   turns, hence a CRITICAL risk verdict whatever the declared risk.
   Warming the estimator (threading only the scientific state)
   halves CRITICAL to 58.3% with 41.7% WARN and moves no final
   verdict at all on this family: the monitor's risk verdict is
   observability, not gating, on D. At the default
   $\delta = 0.01$, certifying OK ($\leq 0.15$) needs on the order
   of 100 clean turns; 24-turn trajectories cannot reach it.
4. **The composite fast-energy shortcut discards slow coupling
   exactly when the state is complete** (found in LOT B1): on
   complete quadruples the gate consumes the fast energy directly
   and the slow term only enters on incomplete states. The corpus
   therefore exercises the fast path; the slow-coupling term of M7
   remains validated only by unit fixtures. Campaign MATH-C measured
   the full-W variant on D-1.0 before deciding (LOT C2): wiring
   W = V + lambda*mismatch everywhere breaks the registered ISS
   bound (sup W 8.81 against 6.0, the mismatch term dominating),
   moves 57 of 1440 verdicts in BOTH directions (37 relaxations, 20
   tightenings, so not a hardening-only change under F-001), lifts
   nominal contraction from 0.516 to 0.592 without passing, and
   shrinks the measured conservative small-gain margin from 0.084
   to 0.052. Decision DM-C1 (owner, 2026-09-01): the shortcut is
   the v0 design, kept and documented here; full wiring is re-posed
   at DM4 with lambda calibrated on real traffic rather than the
   arbitrary 0.5.

### 10.6 Sensitivity (LOT B4)

Published in `sweeps.json`:

- **Adaptive veto edge (margin 0)**: 92.3% of available margins sit
  above the edge; only 11.3% sit within +-0.02 of it. The veto's
  dominance on D is structural, not a hair-trigger boundary effect;
  moving the critical/warning band edges (-0.02, -0.05) reallocates
  under 4% of mass.
- **Collapse-abstain threshold 0.8**: flip mass at most 1.5% across
  alternates 0.7 to 0.9; the collapse signal is close to bimodal on
  D and the threshold choice is robust there.
- **Risk-verdict ceilings on the warm variant**: the ok ceiling
  (0.10/0.15/0.20) changes nothing on D (the UCB never gets low
  enough); the critical ceiling (0.30/0.40/0.50) moves the
  CRITICAL/WARN split (100%/58%/38% CRITICAL) and, on this corpus,
  never a final verdict.

### 10.7 What this campaign does not establish

Section 8's list stands. In particular: no claim about production
or veramem traffic (the corpus is synthetic and its nominal dynamics
proved exogenous rather than contracting); no adversarial-robustness
claim beyond the corpus's schema-level adversarial family; no
calibration of runtime defaults (DM-B1, DM4); and the ALLOW side of
the gate distribution is untested at this level because ALLOW is
unreachable on cold synthetic turns by design of the provenance and
monitoring guards.

---

## 11. Campaign 2 Report: MATH-C, 2026-09-01 (corpus D-2.0)

### 11.1 Why a second corpus

Section 10.2's failed criterion taught that on an exogenous input
walk, contraction dominance measures the corpus, not the kernel.
D-2.0 encodes A12's contraction regime in the input dynamics: a new
``nominal_feedback`` family whose fast input channels start stressed
and relax geometrically toward published targets, faster when the
previous final verdict tightened (the complete loop: verdict back
into input). The law's constants are published as ``FEEDBACK_LAW``
in ``validation/m10/corpus.py`` and executed by the harness; the
seven D-1.0 families are regenerated under D-2.0's own master seed
(20260902) as controls. 64 trajectories, 1632 turns, bit-for-bit
reproducible.

### 11.2 Registration and judgment

The campaign 2 criteria (``PROPOSED_D2``) are the registered D-1.0
set with one change, published before any run: 5.1 judges the
feedback family. The owner registered the set unmodified on
2026-09-01 (DM-C2), before the first full D-2.0 run.

**12 of 12 criteria passed**, including:

| Criterion | Registered | Observed |
|---|---|---|
| 5.1 feedback contraction dominates | >= 0.60 | **1.000** |
| 5.1 bounded expansion | <= 1.50 | 0.554 |
| 5.2 no divergence / bounded energy | == 0, <= 6.0 | 0, 1.563 |
| 5.3 estimator availability | >= 0.50 | 0.848 |
| 5.4 ABSTAIN never relaxed (M6) | == 0 | 0 |
| 5.5 adversarial ALLOW, expansion ALLOW | <= 0, <= 0.05 | 0.0, 0.0 |
| 5.7 negative feedback consistency | >= 0.95 | 1.00 |

### 11.3 The treatment/control contrast

The same run carries both nominal families:

- ``nominal_feedback`` (contraction encoded in inputs):
  p_contraction **1.000**;
- ``nominal`` (exogenous walk, the D-1.0 control): p_contraction
  0.495.

This is the D-1.0 lesson demonstrated in one experiment: the
projection-to-energy chain tracks the input dynamics faithfully, and
the 5.1 criterion is meaningful exactly when the corpus declares
what the inputs do.

### 11.4 The adaptive layer discriminates in both directions

On D-1.0 the revived adaptive layer vetoed almost everything (bands:
hard 1107 of 1200 available turns; final verdict by hard veto on 952
of 1248 threaded turns) because the corpus energy did not contract.
On D-2.0's feedback family the same layer, unchanged, reads the
contracting energy and stands down: bands hard 16 / critical 66 /
warning 77 / stable 25, ABSTAIN 10.9% and REQUIRE_CONFIRMATION 89.1%
on the family. Together the two campaigns show the DM-B0 layer is
not a constant brake: it responds to measured contraction in both
directions, which is the behavior A12 asks of it. ALLOW remains 0.0
corpus-wide (the provenance and cold-monitoring floors of section
10.3, unchanged by design).

### 11.5 Reproduction

``python -m validation.m10 run2`` regenerates the campaign 2
artifacts under ``validation/m10/artifacts_d2/`` (the per-turn
measurements are untracked and regenerate identically). The gate
pins the D-2.0 identity: the eight families as a literal, manifest
reproducibility, and the deterministic contracting transient of the
feedback family.

Scope of the byte-identity guarantee, sharpened by the first
third-party reproduction: the owner's macOS arm64 run reproduced
every manifest and judgment byte-for-byte but drifted a single
double by one ulp (a family ``sup_w_max``, 0.9532080249999999
against 0.953208025) relative to the Linux x86-64 reference, the
signature of fused-multiply-add reductions in the numeric backend.
Aggregates absorb such noise; a raw ``max`` publishes it. Published
artifacts are therefore serialized with floats rounded to 12
decimals, far above the 1e-16 relative ulp noise and far below any
scientific meaning in these metrics; internal judge comparisons
stay raw. Determinism is exact within a platform, and the published
text is now identical across platforms.

## 12. Campaign 3 Report: ALLOW, 2026-09-02

### 12.1 The defect: a drift magnitude read as an energy derivative

Sections 10.3 and 11.4 both closed on the same observation, treated
as a design floor: ALLOW was never observed as a final verdict, 0
times across the 3072 turns of campaigns 1 and 2. That reading was
wrong. The floor was a defect in the projection certificate.

``ProjectionValidator`` assessed ``lyapunov_compatibility_ok``
against the composite energy delta, and fell back to the private
``ctx._dv`` attribute when no delta was available:

```python
delta_w = delta_w_of(ctx)
dv = getattr(ctx, "_dv", None)
if delta_w is not None:
    lyapunov_ok = float(delta_w) <= self.lyapunov_positive_threshold
elif dv is not None:
    lyapunov_ok = float(dv) <= self.lyapunov_positive_threshold
```

Two facts make the fallback a defect rather than a degraded mode.

``ctx._dv`` is written by the core stage as
``float(core_ctx.drift_score)``, and ``DriftSignal.__post_init__``
stores ``clamp01(abs(value))``. The value is a magnitude in [0, 1]
and is never negative, so ``dv <= 1e-9`` held only when drift was
exactly zero. Any drift at all was published as a measured Lyapunov
incompatibility. The suite's own fixtures record the intent that was
lost: the sibling test seeded ``_dv = -0.1``, a value the clamp makes
unreachable in the running system, which is the clearest evidence
the branch was written against a signed derivative that never
arrived on that attribute.

And ``composite.delta_w`` is written by the gate stage, which runs
after the projection stage. On the certificate the gate consumes,
the delta is therefore always ``None``. The fallback was not an edge
case: it was the branch taken on every certified turn. Instrumented
over campaign 2, ``ProjectionValidator.validate`` was called 3264
times for 1632 turns, and every one of the 1632 pre-gate calls took
the fallback. The second call per turn is
``PipelineObservabilityService``, which refreshes the certificate
during finalize, after the verdict is decided: the corrected
certificate existed, but only in the observability export, never in
the decision.

The consequence chain is mechanical:

```
lyapunov_compatibility_ok = False
  -> is_projection_safe = False
      -> projection_unsafe                    (soft floor on ALLOW)
      -> projection_available = False          in the validity envelope
          -> validity_projection_unavailable   (second floor)
```

### 12.2 Effect on both campaigns

The axis is now assessed only against the composite delta. When no
delta is available it is reported unassessed in ``checks_detail``
and excluded from the certification level, which is the treatment
noise robustness and mode stability already receive (section 5.9). A
delta that is present but uncoercible stays fail-closed under F-002.

| | D-1.0 before | D-1.0 after | D-2.0 before | D-2.0 after |
|---|---|---|---|---|
| ``projection_unsafe`` | (see note) | **0** | 1270 | **0** |
| ``projection_lyapunov_incompatible`` | (see note) | **0** | 1270 | **0** |
| ``validity_projection_unavailable`` | (see note) | 131 | 1394 | 124 |
| envelope alive in domain | 0.1757 | **1.000** | 0.1578 | **1.000** |
| ABSTAIN | 0.85625 | **0.85625** | 0.782475 | **0.782475** |
| REQUIRE_CONFIRMATION | 0.14375 | 0.128472 | 0.217525 | 0.213848 |
| ALLOW | 0.0 | **0.015278** | 0.0 | **0.003676** |

Note: the per-turn measurement files are untracked (section 11.5),
so the before counts are reported for the corpus on which they were
instrumented live during the investigation. The envelope rate is a
tracked metric and carries the same evidence on both corpora.

The registered judgments are unchanged: **11 of 12 on D-1.0 and 12
of 12 on D-2.0**, the same criteria passing and the same one
failing.

### 12.3 What the relaxation did and did not touch

This campaign lifts a floor, which under F-001 requires the floor to
be shown illegitimate rather than merely inconvenient. The measured
containment:

- **ABSTAIN is bit-identical on both corpora**, 1233 and 1277 turns.
  No refusal was relaxed. The change moves REQUIRE_CONFIRMATION to
  ALLOW and nothing else.
- ALLOW appears in two families only, ``nominal`` (15 and 4) and
  ``long_horizon`` (7 and 2). The ``adversarial``, ``conflicting``,
  ``boundary``, ``declared_risk``, ``switching_stress`` and
  ``nominal_feedback`` distributions are unchanged to the digit.
- Criterion 5.5 (adversarial never ALLOW) still observes 0.0, and it
  now observes it on a system where ALLOW is reachable, which is the
  first campaign in which that criterion carries information.
- Every ALLOW turn has a strictly negative composite delta, from
  -0.0575 to -0.4148.

Conditional on a contracting turn, ALLOW reaches 0.0381 overall and
0.1579 on the nominal family of D-1.0.

### 12.4 A threshold that has stopped discriminating

``envelope_compliance.envelope_alive_in_domain`` was registered at
>= 0.10 and observed 0.1757 and 0.1578. Those numbers were the
defect: the validity envelope was dead on roughly five turns out of
six inside its own domain. It now observes 1.000 on both corpora.

The criterion still passes, but at a threshold it can no longer
fail. It is recorded here as non-discriminating and must be
re-registered before campaign 4 rather than carried forward as
evidence. Registering a replacement now, after seeing the result,
would be exactly the post-hoc move section 9 forbids.

### 12.5 What ALLOW still requires

ALLOW is reachable, and it is still not the outcome of an ordinary
quickstart turn. Measured on the public ``ArvisEngine`` contract, 40
threaded turns of plain text prompts return REQUIRES_CONFIRMATION
throughout, with ``delta_w`` at ``None`` on every turn: a bare
informational input produces the minimal certificate of section 3.3,
so there is no measured contraction to certify. The defect this
campaign closed affected structured, certified turns; it never
touched the bare-prompt path, which floors for the honest reason.

The two conditions that remain, both documented in
``docs/PATH_TO_ALLOW.md``:

1. the switching dwell clock still cannot cross the public contract,
   so a host driving the engine accumulates no dwell time;
2. ``delta_w_soft_threshold`` (-0.05) floors a contraction that is
   real but weaker than the threshold, with reason
   ``weak_stability``. On D-2.0 that single condition accounts for
   108 of the 113 turns where the gate says ALLOW and the final
   verdict does not. The constant is conventional; the campaigns now
   provide the ΔW scale needed to calibrate it, and that calibration
   is a dedicated change with its own registration.

### 12.6 Reproduction

``python -m validation.m10 run`` and ``run2`` regenerate both
campaigns. Mutation replay on the certificate surface: 7 mutants, 6
killed. The survivor, folding the unassessed axis back into the
certification level, is an equivalent mutant: no reachable state has
``lyapunov_assessed`` false while ``lyapunov_ok`` is false, so no
test can distinguish it. It is reported rather than papered over
with a pin that would assert nothing.

## 13. Campaign 4 Report: PROJ, 2026-09-02

### 13.1 Scope

Three coherence defects on the projection and switching path, fixed
in one campaign because they compound: an operator reacting to a
misread signal perturbs the view the certificate validates, a
post-decision refresh rewriting that certificate falsifies the trace
of the perturbed decision, and a clock ticking twice per turn feeds
the guard that floors the result. Zero veramem contact.

### 13.2 The operator reacted to the same misread signal (DM-P1)

``PiOperator`` clamped its blending strength to 0.6 whenever
``ctx._dv`` was positive, reading it as a signed divergence. Campaign
12 established the attribute carries the drift score, a magnitude in
[0, 1]: the clamp fired on 85 per cent of campaign 2 turns and the
light alpha = 1.0 branch was reachable only at exactly zero drift
(248 of 1632 turns). The measured drift distribution (median 0.048,
maximum 0.283) also settles the alternative that was considered:
reinterpreting the thresholds against the magnitude at the declared
``is_high`` level (0.7) would never fire, dead code with
unregistered constants. The reaction is removed; drift-reactive
projection strength is re-posed at DM4 with a real signal.

Effect, measured before pinning: no verdict moves on either corpus,
both judgments unchanged, and about 20 spurious
``projection_boundary`` flags disappear per corpus (464 to 444 on
D-1.0, 467 to 447 on D-2.0).

### 13.3 The published certificate was not the one that decided (DM-P2)

The observability refresh ran the full projection again during
finalize and overwrote every decision field, certificate included.
Measured on the smoke corpus: the published certificate differed
from the one the gate consumed on 42 turns of 42, materially on 18
(LOCAL with the Lyapunov axis unassessed at decision time, BASIC
with ``lyapunov_compatibility_ok`` False in the trace). The IR
adapter read the published one, so the audit trail contradicted the
decision.

The refresh is now a post-hoc attestation: it re-validates the
DECISION'S OWN VIEW against the signals that only exist after the
gate, which is also the first place the Lyapunov axis is assessed
with the real composite delta, and publishes under distinct names
(``post_certificate``, ``projection_post_certification_level``,
``projection_post_lyapunov_compatible``). What decided is never
rewritten. The overwrite had no test pin, one more measure of the
distance between this path and the suite's reach.

### 13.4 The dwell clock ticked twice per turn

``regime_stage`` (before the gate) and ``runtime_stage`` (after it)
both ticked the same ``SwitchingRuntime``, so tau_d counted two per
turn and the guard's left-hand side ln(J)/tau_d was HALF its true
value: switching was declared safe with half the dwell actually
served. This is the campaign's only behavioral change and it is
anti-conservative in the defect, conservative in the fix. The single
owner is now ``runtime_stage``, post-decision, so the guard reads
the dwell of completed turns.

Verdict movement, entirely attributable to this half (decomposition
run with the blob restore disabled gives identical numbers):

| | D-1.0 before | D-1.0 after | D-2.0 before | D-2.0 after |
|---|---|---|---|---|
| ABSTAIN | 1233 | 1260 | 1277 | 1391 |
| REQUIRE_CONFIRMATION | 185 | 169 | 349 | 237 |
| ALLOW | 22 | **11** | 6 | **4** |

The movement is monotone hardening on a corrected clock: no ABSTAIN
was relaxed anywhere, and the ALLOW that remain (nominal 7 and 4,
long_horizon 4 and 1 per corpus) sit on the same contracting-turn
profile as before. Both registered judgments hold, 11 of 12 and 12
of 12, with ``adaptive_estimation.estimator_availability`` easing
from 0.848 to 0.814 on D-2.0, well above its 0.5 threshold. The
campaign 3 ALLOW counts (22 and 6) were measured on the inflated
clock and are superseded by this table.

### 13.5 The dwell clock crosses the public contract

The clock lived on a runtime rebuilt fresh per pipeline; only a deep
integration owning the pipeline could carry it, which is exactly
what the M10 harness does (its threading loop carries the runtime
object). A host on the documented ``ArvisEngine`` contract could
never accumulate dwell, so ``switching_unsafe_monitoring`` never
went away for it.

The opaque blob now carries a ``switching`` section, written at
finalize after the turn's completed regime update and restored at
``core_stage``, the single ingestion point of the host blob (the
extra-read ratchet refused a second read site, working as designed).
``SwitchingRuntime`` owns its own (de)serialization the way the
monitor owns the rest of the blob; a blob without the section, or
with a malformed one, degrades to a fresh clock. Campaign artifacts
regenerate identically under threading because the harness already
carried the clock: the campaign numbers isolate the tick fix, and
the engine-level pins measure the contract: tau_d accumulates across
threaded public turns and the cold-monitoring reason disappears,
which no ``ArvisEngine`` host could reach before.

### 13.6 Reproduction

``python -m validation.m10 run``, ``run2`` and ``sweep`` regenerate
the artifacts. Mutation replay on the three surfaces is recorded in
the campaign closure; the moved tests are
``test_pi_operator_reacts_to_divergence`` (pinned the drift clamp)
and ``test_regime_stage.py::test_full_flow`` (pinned the double
tick).
