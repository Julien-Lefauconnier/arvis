# ARVIS VFS Specification V1

**Project:** ARVIS  
**Subsystem:** Kernel Core Virtual File System (VFS)  
**Version:** V1  
**Status:** Draft / implementation-aligned specification  
**Date:** 2026-04-14

---

## 1. Purpose

This document defines the **ARVIS kernel VFS subsystem** as integrated during the current implementation cycle.

The goal of this specification is to establish a stable reference for:

- the VFS kernel domain model,
- the VFS service invariants,
- the ZIP import sub-system,
- the syscall surface exposed by the kernel,
- deterministic behavior expectations,
- integration constraints for future backends and runtime layers.

This is not an HTTP API specification and not an application-layer storage specification. It is a **kernel-core subsystem specification**.

---

## 2. Scope

This V1 specification covers:

- logical files and folders,
- in-memory repository contract and baseline implementation,
- canonical tree projection,
- VFS domain exceptions,
- ZIP dry-run analysis,
- ZIP collision detection,
- ZIP planning,
- ZIP execution orchestration,
- VFS and ZIP syscalls,
- syscall service injection through the kernel service registry.

This V1 does **not** define:

- HTTP routes,
- authentication or user identity verification,
- permissions / ACLs,
- persistent database or Qdrant-backed repository drivers,
- content encryption,
- semantic indexing,
- action journal persistence,
- full audit-trail semantics,
- distributed filesystem semantics.

---

## 3. Architectural position inside ARVIS

The VFS is implemented as a **kernel-core subsystem** under:

```text
arvis/kernel_core/vfs/
```

It is exposed to the rest of the system primarily through:

- domain services,
- ZIP orchestration services,
- kernel syscalls.

The VFS syscall layer lives under:

```text
arvis/kernel_core/syscalls/syscalls/vfs_syscalls.py
```

Runtime service injection is handled through:

```text
arvis/kernel_core/syscalls/service_registry.py
```

This keeps the syscall handler scalable and prevents constructor growth as additional subsystems are added.

---

## 4. Design principles

### 4.1 Kernel-first design

The VFS is defined as a pure kernel subsystem, not as a backend feature port.

Consequences:

- no dependency on FastAPI,
- no dependency on backend application settings,
- no dependency on persistence drivers in the domain contract,
- explicit service boundaries,
- deterministic behaviors wherever possible.

### 4.2 Layer separation

The subsystem is split into the following layers:

1. domain models,
2. domain exceptions,
3. repository contract,
4. repository implementations,
5. VFS domain service,
6. tree projection,
7. ZIP models and services,
8. syscall exposure.

### 4.3 Determinism

The subsystem is designed to behave deterministically for equivalent logical input.

This especially applies to:

- tree projection ordering,
- collision detection semantics,
- syscall result shapes,
- replay-policy classification.

### 4.4 Explicit failure semantics

Domain errors are surfaced through explicit VFS and ZIP exception classes and mapped into syscall error codes.

---

## 5. Module layout

Current kernel layout:

```text
arvis/kernel_core/vfs/
├── exceptions.py
├── models.py
├── repositories/
│   ├── __init__.py
│   └── in_memory.py
├── repository.py
├── service.py
├── tree.py
└── zip/
    ├── analyzer.py
    ├── collision.py
    ├── exceptions.py
    ├── executor.py
    ├── guard.py
    ├── models.py
    ├── plan.py
    ├── reader.py
    └── service.py
```

Syscall integration:

```text
arvis/kernel_core/syscalls/
├── service_registry.py
├── syscall_handler.py
└── syscalls/
    ├── tool_syscalls.py
    └── vfs_syscalls.py
```

---

## 6. Core VFS domain model

### 6.1 `VFSItemType`

Defined values:

- `"file"`
- `"folder"`

### 6.2 `VFSItem`

`VFSItem` is the canonical logical item representation.

Fields:

- `item_id: str`
- `display_name: str`
- `item_type: VFSItemType`
- `parent_id: Optional[str]`
- `mime: Optional[str] = None`
- `file_size: Optional[int] = None`
- `created_at: Optional[int] = None`

Behavior helpers:

- `is_file() -> bool`
- `is_folder() -> bool`

### 6.3 Semantics

A `VFSItem` is a **logical node**, not necessarily a persisted content object.

A file item may exist without a content storage backend.

A folder item is a namespace node.

---

## 7. VFS exceptions

The VFS domain uses explicit exception types.

### 7.1 Base exception

- `VFSError`

### 7.2 Concrete VFS exceptions

- `VFSItemNotFoundError`
- `VFSParentNotFoundError`
- `VFSParentNotFolderError`
- `VFSNameConflictError`
- `VFSFolderNotEmptyError`
- `VFSCycleError`
- `VFSInvalidNameError`

### 7.3 Semantics

These exceptions are domain-level failures and are used by the VFS service to signal invariant violations.

They are later mapped to stable syscall error codes.

---

## 8. Repository contract

### 8.1 Contract role

The repository contract defines the persistence boundary for VFS items.

The kernel service depends on the contract, not on a concrete backend.

### 8.2 Required repository methods

A VFS repository must provide:

- `list_items(user_id: str) -> list[VFSItem]`
- `get_item(user_id: str, item_id: str) -> Optional[VFSItem]`
- `create_folder(user_id: str, name: str, parent_id: Optional[str]) -> str`
- `create_file_item(user_id: str, name: str, parent_id: Optional[str], size: Optional[int], mime: Optional[str]) -> str`
- `delete_item(user_id: str, item_id: str) -> None`
- `rename_item(user_id: str, item_id: str, new_name: str) -> None`
- `move_item(user_id: str, item_id: str, parent_id: Optional[str]) -> None`

### 8.3 Current implementation

V1 ships with:

- `InMemoryVFSRepository`

This is the baseline driver used for deterministic tests and kernel validation.

---

## 9. In-memory repository baseline

### 9.1 Storage model

The in-memory repository stores VFS items in a bucket per user.

Conceptually:

- top-level map keyed by `user_id`
- inner map keyed by `item_id`

### 9.2 Repository guarantees

The repository itself does **not** enforce all domain invariants.

It is intentionally thin.

The VFS service is responsible for:

- name validation,
- parent validation,
- collision detection,
- cycle prevention,
- folder non-empty checks.

### 9.3 ID generation

The baseline implementation uses UUIDs for item creation.

This is acceptable for V1 because deterministic ordering in tree projection relies on explicit sorting, not insertion order.

---

## 10. VFS service

### 10.1 Role

`VFSService` is the authoritative domain service for logical filesystem mutations and reads.

### 10.2 Public methods

Current service surface:

- `list_items(user_id)`
- `get_item(user_id, item_id)`
- `create_folder(user_id, name, parent_id)`
- `create_file_item(user_id, name, parent_id, size, mime)`
- `delete_item(user_id, item_id)`
- `rename_item(user_id, item_id, new_name)`
- `move_item(user_id, item_id, parent_id)`

### 10.3 Name normalization

All item names are normalized with `strip()`.

If the normalized name is empty, the service raises:

- `VFSInvalidNameError`

### 10.4 Parent validation

If a `parent_id` is provided:

- the parent must exist,
- the parent must be a folder.

Failures map to:

- `VFSParentNotFoundError`
- `VFSParentNotFolderError`

### 10.5 Name uniqueness invariant

Within a given parent folder, item names are globally unique.

This means the following is forbidden in the same parent:

- file `note`
- folder `note`

Any collision raises:

- `VFSNameConflictError`

### 10.6 Delete invariant

Deleting a file is allowed if the file exists.

Deleting a folder is allowed only if the folder is empty.

If the folder contains children, the service raises:

- `VFSFolderNotEmptyError`

### 10.7 Rename invariant

Renaming an item preserves:

- its identity,
- its type,
- its parent,
- its metadata except display name.

A rename must not create a same-parent conflict.

### 10.8 Move invariant

Moving an item requires:

- target parent exists if provided,
- target parent is a folder,
- no name conflict in the target parent.

For folders, moving into self or a descendant is forbidden.

Such invalid moves raise:

- `VFSCycleError`

---

## 11. Tree projection

### 11.1 `VFSTreeNode`

Tree projection uses `VFSTreeNode`:

- `item: VFSItem`
- `children: list[VFSTreeNode]`

This is a derived structure only.

It is:

- not persisted,
- not indexed,
- not canonical storage.

### 11.2 `build_vfs_tree`

`build_vfs_tree(items)` constructs a stable tree projection from flat VFS items.

### 11.3 Ordering guarantee

Tree nodes are sorted deterministically using this order:

1. folders before files,
2. case-insensitive display name,
3. item id as final tie-breaker.

This deterministic sort is required for:

- reproducible projections,
- stable syscalls,
- replay-friendly behavior.

---

## 12. ZIP subsystem overview

The ZIP subsystem is a VFS-adjacent kernel service used to safely analyze and import ZIP archives.

### 12.1 Major components

- `ZipGuard`
- `ZipSafeReader`
- `ZipAnalyzer`
- `ZipCollisionService`
- `ZipImportPlanService`
- `ZipExecutor`
- `ZipIngestService`

### 12.2 Two-phase model

ZIP import is intentionally split into two phases:

1. **dry-run phase**
   - archive validation,
   - ZIP tree analysis,
   - VFS collision detection.

2. **execution phase**
   - optional user plan application,
   - logical VFS creation,
   - optional content ingestion behavior through executor integration.

This separation is a core invariant of the subsystem.

---

## 13. ZIP models

### 13.1 `ZipNode`

`ZipNode` is the logical in-memory representation of a ZIP tree entry.

Fields:

- `name: str`
- `node_type: Literal["file", "folder"]`
- `parent: Optional[ZipNode] = None`
- `children: list[ZipNode] = []`
- `size: Optional[int] = None`
- `extension: Optional[str] = None`
- `supported: Optional[bool] = None`
- `reason: Optional[str] = None`
- `zip_path: Optional[str] = None`

Helpers:

- `is_file()`
- `is_folder()`
- `add_child(child)`
- `iter_tree()`
- `full_path_debug()`

### 13.2 `ZipCollision`

Represents a single conflict between a ZIP node and an existing VFS item.

Fields:

- `zip_node: ZipNode`
- `vfs_item: VFSItem`
- `reason: ZipCollisionReason`

Current reasons:

- `already_exists`
- `parent_is_file`

### 13.3 `ZipCollisionReport`

Fields:

- `has_conflicts: bool`
- `collisions: list[ZipCollision]`

### 13.4 ZIP plan models

Current kernel ZIP plan types are defined in `zip.models`.

They include:

- `ZipImportPlan`
- `ZipImportPlanEntry`

Supported plan actions are:

- `import`
- `skip`
- `rename`

---

## 14. ZIP security guard

### 14.1 Role

`ZipGuard` is the first security boundary for archive analysis.

It validates archive-level and entry-level constraints before analysis proceeds.

### 14.2 Current security checks

The guard rejects:

- missing archive path,
- non-file archive path,
- non-`.zip` extension,
- corrupted ZIP archive,
- empty archive,
- too many files,
- file entries larger than configured limits,
- excessive total uncompressed size,
- suspicious compression ratio,
- absolute paths,
- path traversal entries,
- blocked executable/script-like extensions.

### 14.3 Blocked extension baseline

The current blocked extension set includes entries such as:

- `.exe`
- `.dll`
- `.bat`
- `.cmd`
- `.sh`
- `.js`
- `.jar`
- `.py`
- `.php`
- `.pl`
- `.rb`
- `.so`
- `.bin`

### 14.4 Security configuration model

V1 uses environment-backed constants inside the guard implementation.

This is acceptable for the current implementation, but the preferred future direction is a dedicated ARVIS-side configuration object for ZIP guard limits.

---

## 15. ZIP safe reader

### 15.1 Role

`ZipSafeReader` provides secure, non-extractive archive access.

### 15.2 Guarantees

It guarantees:

- no extraction to disk,
- normalized relative POSIX paths,
- rejection of absolute paths,
- rejection of path traversal,
- controlled binary file opening.

### 15.3 Public API

- `iter_entries()`
- `open_file(path)`
- context manager support

### 15.4 Entry model

The reader exposes `ZipEntry` with:

- `path: str`
- `size: int`
- `is_dir: bool`

---

## 16. ZIP analyzer

### 16.1 Role

`ZipAnalyzer` performs passive archive analysis and produces a logical `ZipNode` tree.

### 16.2 Important invariants

The analyzer must:

- perform no VFS writes,
- perform no ingest execution,
- avoid disk extraction,
- mark supported and unsupported files,
- produce a virtual root node named `/`.

### 16.3 Supported file types baseline

The current supported extension set includes:

- `.pdf`
- `.txt`
- `.md`
- `.png`
- `.jpg`
- `.jpeg`
- `.docx`
- `.xlsx`
- `.pptx`

Unsupported files remain represented in the tree but are marked with:

- `supported = False`
- `reason = "unsupported_file_type"`

### 16.4 Test behavior

In test environments, guard enforcement may be disabled to simplify unit testing of analyzer logic.

---

## 17. ZIP collision detection

### 17.1 Role

`ZipCollisionService` detects logical conflicts between a ZIP import tree and the current VFS state.

### 17.2 Behavior

The service:

- loads existing VFS items for the user,
- indexes them by parent/name,
- walks the ZIP tree,
- reports conflicts where an item already exists in the target parent,
- reports invalid parent states where a ZIP subtree would descend into a file.

### 17.3 Output

The output is always a `ZipCollisionReport`.

---

## 18. ZIP plan service

### 18.1 Role

`ZipImportPlanService` applies an explicit user plan to a `ZipNode` tree before execution.

### 18.2 Supported actions

- `import`: keep the file unchanged,
- `skip`: remove the file from the effective import tree,
- `rename`: rename the file before execution.

### 18.3 Current semantics

The current plan service acts on file nodes and leaves the virtual root intact.

For rename actions:

- `new_name` is required,
- `/` and `\\` are forbidden in the new name,
- duplicate rename targets are rejected.

### 18.4 Current syscall exposure

The V1 syscall layer now includes:

- `vfs.zip.plan`

Its job is to apply a user-provided plan to a serialized ZIP root and return a transformed serialized ZIP root.

This syscall is **purely structural** and does not execute VFS writes.

---

## 19. ZIP executor

### 19.1 Role

`ZipExecutor` performs the actual import after analysis and optional planning.

### 19.2 Current behavior

The executor:

- traverses the effective ZIP tree,
- creates folders in the VFS,
- creates files in the VFS,
- delegates file ingestion through the configured ingest integration where applicable,
- returns a structured result summary.

### 19.3 Result shape

Current result payload shape is dictionary-based and includes:

- `status`
- `imported_files`
- `skipped_files`
- `created_items`

### 19.4 V1 note

The executor remains the most infrastructure-sensitive part of the ZIP subsystem and is a likely evolution point for future driver abstraction.

---

## 20. ZIP ingest orchestration service

### 20.1 `ZipIngestDecision`

The dry-run result model contains:

- `status: str` where expected values are `ready`, `conflict`, `rejected`
- `zip_root: Optional[ZipNode]`
- `collisions: Optional[ZipCollisionReport]`
- `reason: Optional[str]`

### 20.2 `ZipIngestService`

This service orchestrates the ZIP lifecycle.

#### Public methods

- `analyze_and_validate(...) -> ZipIngestDecision`
- `execute_import(...) -> dict`
- `execute_from_path(...) -> dict`

### 20.3 Dry-run phase

`analyze_and_validate`:

1. analyzes the ZIP,
2. detects collisions,
3. returns one of:
   - `ready`
   - `conflict`
   - `rejected`

### 20.4 Execution phase

`execute_import`:

1. optionally applies the plan,
2. delegates execution to the ZIP executor.

### 20.5 Convenience execution path

`execute_from_path`:

1. runs dry-run validation,
2. raises a ZIP domain exception on invalid state,
3. executes the import when ready.

### 20.6 ZIP execution exceptions

ZIP execution currently uses:

- `ZipIngestError`
- `ZipRejectedError`
- `ZipConflictError`

---

## 21. Kernel service registry integration

### 21.1 Purpose

ARVIS now uses a `KernelServiceRegistry` to inject subsystem services into the syscall layer.

### 21.2 Current registry fields

The registry currently exposes:

- `tool_executor`
- `vfs_service`
- `zip_ingest_service`

### 21.3 Architectural benefit

This avoids constructor growth in `SyscallHandler` and provides a scalable pattern for future kernel subsystems.

Future services can be added without changing the syscall handler signature each time.

---

## 22. Syscall handler integration

### 22.1 Service access pattern

VFS syscalls resolve services through:

- `handler.services.vfs_service`
- `handler.services.zip_ingest_service`

### 22.2 Replay policy classification

The syscall handler currently classifies replay policies as follows:

#### Recompute

- `vfs.list`
- `vfs.tree`
- `vfs.zip.analyze`

These are treated as recomputable read-like syscalls.

#### Journal-only replay

Any `vfs.*` syscall not in the recompute set is treated as a mutating syscall and classified as:

- `journal_only_replay`

This includes write syscalls and ZIP execution/planning syscalls.

### 22.3 Rationale

This policy preserves replay safety by distinguishing:

- read-side structural recomputation,
- state-mutating operations that should be journal-driven.

---

## 23. VFS syscall surface

### 23.1 Read syscalls

#### `vfs.list`

Arguments:

- `user_id`

Returns:

- serialized list of VFS items

#### `vfs.get`

Arguments:

- `user_id`
- `item_id`

Returns:

- serialized VFS item

#### `vfs.tree`

Arguments:

- `user_id`

Returns:

- serialized deterministic VFS tree

### 23.2 Write syscalls

#### `vfs.create_folder`

Arguments:

- `user_id`
- `name`
- `parent_id: Optional[str]`

Returns:

- serialized created VFS item

#### `vfs.create_file`

Arguments:

- `user_id`
- `name`
- `parent_id: Optional[str]`
- `size: Optional[int]`
- `mime: Optional[str]`

Returns:

- serialized created VFS item

#### `vfs.delete_item`

Arguments:

- `user_id`
- `item_id`

Returns:

- deletion summary payload

#### `vfs.rename_item`

Arguments:

- `user_id`
- `item_id`
- `new_name`

Returns:

- serialized updated VFS item

#### `vfs.move_item`

Arguments:

- `user_id`
- `item_id`
- `parent_id: Optional[str]`

Returns:

- serialized updated VFS item

### 23.3 ZIP syscalls

#### `vfs.zip.analyze`

Arguments:

- `zip_path`
- `user_id`
- `target_parent_id: Optional[str]`

Returns:

- serialized `ZipIngestDecision`

#### `vfs.zip.plan`

Arguments:

- `zip_root` (serialized ZIP root)
- `plan` (serialized ZIP import plan or typed plan)

Returns:

- transformed serialized ZIP root

Semantics:

- no VFS write,
- no archive re-read required,
- pure structural transformation.

#### `vfs.zip.execute`

Arguments:

- `zip_path`
- `user_id`
- `target_parent_id: Optional[str]`
- `keep_zip: bool = False`
- `plan: Optional[ZipImportPlan]`

Returns:

- structured execution result dictionary

---

## 24. Syscall serialization rules

### 24.1 VFS item serialization

A VFS item is serialized as:

- `item_id`
- `display_name`
- `item_type`
- `parent_id`
- `mime`
- `file_size`
- `created_at`

### 24.2 Tree serialization

A tree node is serialized as:

- `item`
- `children`

### 24.3 ZIP node serialization

A ZIP node is serialized with:

- `name`
- `node_type`
- `size`
- `extension`
- `supported`
- `reason`
- `zip_path`
- `children`

### 24.4 ZIP decision serialization

A ZIP decision is serialized with:

- `status`
- `reason`
- `zip_root`
- `collisions`

---

## 25. Syscall error mapping

### 25.1 VFS syscall error codes

The syscall layer maps VFS exceptions to stable string codes:

- `VFSItemNotFoundError` → `vfs_item_not_found`
- `VFSParentNotFoundError` → `vfs_parent_not_found`
- `VFSParentNotFolderError` → `vfs_parent_not_folder`
- `VFSNameConflictError` → `vfs_name_conflict`
- `VFSFolderNotEmptyError` → `vfs_folder_not_empty`
- `VFSCycleError` → `vfs_cycle_error`
- `VFSInvalidNameError` → `vfs_invalid_name`

Missing VFS service resolves to:

- `no_vfs_service`

### 25.2 ZIP syscall error codes

The syscall layer maps ZIP exceptions to:

- `ZipRejectedError` → `zip_rejected`
- `ZipConflictError` → `zip_conflict`

Missing ZIP ingest service resolves to:

- `no_zip_ingest_service`

### 25.3 Fallback behavior

Unknown exceptions currently fall back to:

- `"{ExceptionType}:{message}"`

This is acceptable in V1, though future versions may normalize these more aggressively.

---

## 26. Determinism and replay notes

### 26.1 Deterministic tree projection

Deterministic sorting in `build_vfs_tree` is a hard requirement.

### 26.2 Read/write syscall distinction

Replay policy classification distinguishes read-like and write-like VFS syscalls.

### 26.3 ZIP plan purity

`vfs.zip.plan` is intentionally pure and should remain free of side effects.

This makes it an important deterministic transformation point in the ZIP flow.

### 26.4 Current limits

The in-memory repository uses UUID-based item ids, so exact ids are not reproducible across independent fresh runs. Determinism at V1 is therefore defined primarily around:

- invariant enforcement,
- ordering,
- structural results,
- syscall semantics.

---

## 27. Current tested coverage

The subsystem is backed by dedicated tests under:

```text
tests/kernel_core/vfs/
```

Current coverage includes:

- VFS service,
- VFS tree projection,
- ZIP analyzer,
- ZIP collision detection,
- ZIP guard,
- ZIP planning,
- ZIP reader,
- ZIP service orchestration,
- VFS syscalls.

The syscall handler integration is also covered in the kernel-core syscall test suite.

---

## 28. Known implementation gaps and future evolution

### 28.1 Repository backends

Future versions may add:

- persistent SQL repository,
- Qdrant-backed metadata driver,
- object storage metadata bridge.

### 28.2 Security hardening

Future versions should formalize ZIP security configuration in a dedicated ARVIS config model rather than environment-backed constants embedded directly in the guard.

### 28.3 Permissions

No permissions model exists in V1.

### 28.4 Content import abstraction

The ZIP executor should likely evolve toward a cleaner content importer protocol with stricter interface boundaries.

### 28.5 Timeline and audit integration

The VFS currently integrates through syscall journaling and runtime event emission indirectly. A future version could add explicit VFS event models.

### 28.6 Action layer alignment

`arvis/action/catalog/vfs_actions.py` exists and provides a strong basis for future policy coupling, but action-policy integration is not part of V1.

---

## 29. Normative implementation guidance

Any future implementation claiming compatibility with **ARVIS VFS Specification V1** should satisfy the following requirements:

1. it must expose the VFS domain model and invariant behavior defined here,
2. it must preserve same-parent unique naming,
3. it must preserve folder non-empty deletion protection,
4. it must preserve cycle prevention on folder moves,
5. it must preserve deterministic tree ordering,
6. it must expose the documented syscall semantics,
7. it must provide the documented syscall error mappings or stricter equivalents,
8. it must preserve the two-phase ZIP import model,
9. it must preserve the purity of ZIP planning,
10. it must not introduce hard dependencies from the kernel VFS domain to application HTTP frameworks.

---

## 30. Minimal compliance checklist

### Core VFS

- [ ] `VFSItem` model implemented
- [ ] explicit VFS exception hierarchy implemented
- [ ] repository contract implemented
- [ ] same-parent unique naming enforced
- [ ] delete-folder-if-empty-only enforced
- [ ] cycle prevention on move enforced
- [ ] deterministic tree sort enforced

### ZIP

- [ ] ZIP guard implemented
- [ ] ZIP safe reader implemented
- [ ] ZIP analyzer implemented
- [ ] ZIP collision detection implemented
- [ ] ZIP plan service implemented
- [ ] ZIP ingest service implemented
- [ ] ZIP execution service implemented

### Syscalls

- [ ] `vfs.list`
- [ ] `vfs.get`
- [ ] `vfs.tree`
- [ ] `vfs.create_folder`
- [ ] `vfs.create_file`
- [ ] `vfs.delete_item`
- [ ] `vfs.rename_item`
- [ ] `vfs.move_item`
- [ ] `vfs.zip.analyze`
- [ ] `vfs.zip.plan`
- [ ] `vfs.zip.execute`

### Runtime integration

- [ ] service registry wiring in syscall handler
- [ ] replay policy classification present
- [ ] syscall results serializable

---

## 31. Conclusion

The ARVIS VFS subsystem is now no longer a migration idea or a backend extraction draft. In V1 form, it exists as a real kernel-core subsystem with:

- a stable domain model,
- explicit invariants,
- a deterministic tree projection,
- a secure ZIP analysis path,
- a structured ZIP orchestration flow,
- a scalable syscall integration pattern through a service registry.

This V1 forms a strong base for future work on:

- persistent drivers,
- audit and timeline enrichment,
- policy integration,
- permission models,
- cognitive document flows,
- broader ARVIS kernel resource semantics.

