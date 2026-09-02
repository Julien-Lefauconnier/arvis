# Configuration

Every environment variable ARVIS reads, in one place. Nothing else in
the package reads the ambient environment: a contract test
(`tests/contracts/test_env_configuration_registry.py`) fails the gate
if an `os.getenv` / `os.environ` read appears in `arvis/` outside this
registry, so this document cannot silently go stale.

Doctrine (campaign HARDEN, DM-H6): every variable is read lazily (at
use, never at `import arvis`), validated where a malformed value could
weaken a guarantee (a bad value is a typed error naming the variable,
never a silent default), and prefixed `ARVIS_`. The pre-existing
unprefixed ZIP names stay honored during the beta as a deprecated
fallback and will be removed after the deprecation window of
VERSIONING.md.

## ZIP ingestion limits (governed syscall `vfs.zip.*`)

Resolved when a `ZipGuard` is constructed. The prefixed name wins over
the legacy fallback; a malformed or non-positive value raises
`ZipConfigurationError`. The effective limits are part of
`config_fingerprint` (a deployment that loosens a cap is a differently
governed deployment). A caller needing different limits injects a
configured `ZipGuard` at the call site, which always wins over the
environment.

| Variable | Legacy fallback (deprecated) | Default | Type |
|---|---|---|---|
| `ARVIS_ZIP_MAX_TOTAL_SIZE` | `ZIP_MAX_TOTAL_SIZE` | 524288000 (500 MiB) | positive int, bytes |
| `ARVIS_ZIP_MAX_FILE_COUNT` | `ZIP_MAX_FILE_COUNT` | 5000 | positive int |
| `ARVIS_ZIP_MAX_FILE_SIZE` | `ZIP_MAX_FILE_SIZE` | 104857600 (100 MiB) | positive int, bytes |
| `ARVIS_ZIP_MAX_COMPRESSION_RATIO` | `ZIP_MAX_COMPRESSION_RATIO` | 100.0 | positive float |

## Strictness switches

| Variable | Default | Read | Effect |
|---|---|---|---|
| `ARVIS_REASON_STRICT` | `false` | lazily, per normalization | `true`: an unknown reason code raises instead of passing through prefixed. Monotone: it can only make runs stricter. |
| `ARVIS_STRICT_STABILITY` | `false` | lazily, at pipeline bootstrap | `true`: enables the strict stability profile. Monotone with the explicit `strict_mode` argument: either channel can enable, neither can disable the other. |

## LLM provider selection (adapters layer)

| Variable | Default | Read | Effect |
|---|---|---|---|
| `ARVIS_LLM_PROVIDER` | `mock` | lazily, at provider resolution | Selects the LLM provider when the host resolves from the environment. |
| `ARVIS_LLM_MODEL` | unset | lazily, at provider resolution | Model identifier passed to the selected provider. |

None of these variables can weaken a guarantee: the ZIP limits are
validated fail-closed, and both strictness switches are monotone
(enable-only). No variable is read at import time.
