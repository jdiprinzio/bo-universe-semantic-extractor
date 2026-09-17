# Milestone 2B Architecture Simplification Report

## Root cause pattern

All 11 prior patches were PowerShell-Java integration defects (JSON schema/whitespace mismatches, `Start-Job` runspace/parameter issues, log contention, handoff ordering, missing imports, diagnostics serialization) — never SAP discovery logic. `Invoke-InformationalNativeCommand` is a script-scope function and is not visible inside `Start-Job`'s isolated runspace, causing the reported failure.

## Change

`ProviderDiscoveryProbe.java` now performs JAR discovery (`Files.walkFileTree` under SAP install root and IDT plugin directory), provider-family filtering with exclusion evidence, class enumeration, `URLClassLoader` reflection, assignability matching, per-class failure tolerance, `PROBE_SCOPE` counters/heartbeats, and `related_return_type_inventory.json` — all inside one JVM. Progress logs go to stdout and `discovery_progress.log`, written only by this process (single writer).

`run-provider-discovery.ps1` is now path validation → `javac` compile (exit-code-only) → one `java -Xmx4g` invocation with 3 arguments (SAP root, IDT plugin dir, output dir). No `Start-Job`, no handoff files, no `ConvertFrom-Json`.

Removed as obsolete: `provider-scan-handoff.ps1`, `failure-diagnostics.ps1`, `simulate-provider-discovery.ps1`, and 8 stale patch/hotfix contract test files whose subject matter (PowerShell orchestration) no longer exists. Added `test_route_b_milestone_2b_simplified_contract.py`.

## Validation

- Full suite: **147 passed**.
- Import validator: **2 passed** (StandardCharsets import confirmed present).
- Ruff: **All checks passed**.
- Mypy: **7 errors**, all pre-existing/unrelated (`test_query_panel_outline_parser.py`, `test_bo_rest_contract.py`, `test_cli_contract.py`); zero in Route B code.
- Package: source-only, no SAP JARs, no orchestration modules, portable.
