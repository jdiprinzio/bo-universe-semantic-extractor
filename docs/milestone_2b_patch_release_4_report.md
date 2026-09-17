# Milestone 2B Patch Release 4 Report

## Changes

- Replaced the PowerShell-to-Java class-candidate handoff with `included_jars.json`, containing the complete filtered JAR list.
- PowerShell now filters JARs only; it no longer opens archives or selects classes.
- `ProviderDiscoveryProbe` opens every included JAR, enumerates every class entry, converts paths to class names, and loads classes through a `URLClassLoader` with initialization disabled.
- Declared methods are matched by assignable return type. `provider_candidates.json` is now probe output containing identified provider methods.
- Added `PROBE_SCOPE` heartbeat and counter output, filtered-count versus probe-JAR guard, and an average class-per-JAR fail-closed guard using `PROBE_SCOPE_MISMATCH`.
- Scope counters are persisted before the small-enumeration guard fails.

## Safety and Validation

The package remains read-only, performs no CMS or HANA access, instantiates no SDK objects, and contains no SAP binaries or universe artifacts. Java source remains Java 8-compatible.

Source and packaged PowerShell parsing passed. Focused Route B contracts: `41 passed`. Full repository suite: `161 passed, 0 failed`. Package audit: no SAP JARs, universe artifacts, or credential material. The package was regenerated from repository-owned source files.
