# Milestone 2B Hotfix 3 Report

## Missing import added

`import java.nio.charset.StandardCharsets;` added to `ProviderDiscoveryProbe.java`, resolving the 4 identical `cannot find symbol: StandardCharsets` errors at the reported lines.

## Java audit findings (all 10 current source files)

`StableJson.java`, `SecretRedactor.java`, `SdkClasspathValidator.java`, `RequiredInputException.java`, `ReadOnlyPolicy.java`, `Milestone2aProbe.java`, `ExporterConfig.java`, `RouteBMain.java`, `RouteBExporter.java` — no missing imports. `ProviderDiscoveryProbe.java` — missing `StandardCharsets` (fixed). Separately, the packaged `dist` copy still contained a stale, unused `JsonTextParser.java` (an 11th file) left over from an earlier hotfix; it has been deleted from the package.

## Import validator and mutation result

Added `tools/java_import_validator.py`, a javac-free static parser (package/import/declared-type aware, cross-file same-package resolution, `java.lang` allowlist), wired into `tests/contract/test_java_import_validator_contract.py`. Mutation: removing the `StandardCharsets` import → validator reports `ProviderDiscoveryProbe.java:120 missing StandardCharsets` (fail). Restoring it → 0 findings (pass).

## Diagnostics serialization fix and mutation result

Extracted `Write-FailureDiagnostics` into `failure-diagnostics.ps1`: log lines are coerced with `[string]$_`, `probe_scope` copies only 5 known scalar counters (never the raw `ConvertFrom-Json` object), and the whole writer is wrapped in try/catch with a plain-text fallback. New test `tests/powershell/test-failure-diagnostics-serialization.ps1` builds a realistic multi-line-log/scope fixture. Fixed version: `Failure diagnostics serialization test passed` (exit 0). Mutation (original code restored): the writer never completed on the same fixture — reproducing the reported defect (worse than the reported exception; it hung), confirming the fix's necessity.

## Error code and preflight phase

`JAVA_COMPILATION_FAILURE` added as distinct from `CLASSPATH_FAILURE`. New `JAVA_COMPILE_PREFLIGHT` phase compiles all probe sources immediately after tool/path checks and before `JAR_INVENTORY`, using the existing exit-code-only native helper (stderr notes non-fatal). Its output is reused for the probe invocation instead of recompiling later.

## Validation results

- Full suite: `188 passed`.
- 152-JAR simulation: `SIMULATION_PASSED` (`included=152`).
- Import validator + diagnostics tests: passing, both mutation-verified.
- Ruff: `All checks passed!`.
- Mypy: `7` pre-existing/unrelated errors only.
