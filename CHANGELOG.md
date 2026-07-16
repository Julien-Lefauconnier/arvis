
# Changelog

All notable changes to ARVIS are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [PEP 440](https://peps.python.org/pep-0440/)
versioning during the alpha.

## [Unreleased]

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
  egress policy. Defaults preserve prior tool behavior. `examples/05` extended
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
