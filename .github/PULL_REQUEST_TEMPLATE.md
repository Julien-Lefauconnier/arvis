## What this changes

State what breaks without it, and how you know.

## Surface touched

- [ ] Public API (`arvis.__all__`)
- [ ] Effect path (syscalls, tools, capabilities)
- [ ] Canonicalization, commitment or confirmation format
- [ ] None of the above

Anything ticked above changes who reviews this, and the first three carry a
format or deprecation obligation. See VERSIONING.md.

## Checks

- [ ] `bash scripts/run_quality_gate.sh` is green
- [ ] A test fails without this change, not merely one that exercises it
- [ ] English throughout, no em dashes
- [ ] No module added that nothing imports
- [ ] Documentation updated where the behaviour it describes moved

## Ratchets

If a ratchet was relaxed (module reachability, context facade, broad-except,
public API surface), say which, and why relaxing it is the point of this pull
request rather than a way to make it pass.
