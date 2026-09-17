# Milestone 2B Consolidated Hardening Report

## Handoff Format

PowerShell-to-Java inputs now use BOM-free UTF-8 line files:

- `included_jars.txt`: one absolute included JAR path per line.
- `confirmed_classes.txt`: one confirmed fully qualified class name per line.

The JSON files remain human-readable evidence or probe output only. Java no longer parses capability or included-JAR JSON.

## Simulation Harness

`simulate-provider-discovery.ps1` creates synthetic JARs, applies provider filtering, writes both line handoffs, and validates round-trip counts without SAP binaries or Java. The simulation passed with three synthetic JARs, two included, one excluded, and matching handoff counts.

## Hardening

Added explicit handoff preflight logging and aggregate failure checks, no-BOM writers, collection array semantics, and `failure_diagnostics.json` containing phase/error details, handoff sizes/counts, available scope counters, Java version/tool context, and the last 20 progress lines.

Existing read-only behavior, filtering, single-writer logging, time-based heartbeats, URLClassLoader reflection, assignability matching, class-load tolerance, scope guards, stderr-safe execution, and package portability remain enforced.

## Validation

- PowerShell parsing: passed.
- Consolidated Route B contracts: `53 passed`.
- Full repository suite and package audit are the final release checks.
