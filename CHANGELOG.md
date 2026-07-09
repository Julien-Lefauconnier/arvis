
# Changelog

All notable changes to ARVIS are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [PEP 440](https://peps.python.org/pep-0440/)
versioning during the alpha.

## [Unreleased]

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
