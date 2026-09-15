# Milestone 2A Patch Release 5 Report

## Fixes

1. Native executable handling now uses `System.Diagnostics.Process` with separately redirected
   stdout/stderr and explicit process exit-code evaluation. Java/javac/javap informational stderr
   cannot become a PowerShell terminating error; only a non-zero exit code fails the step.
2. Candidate discovery is exact-name-only and prioritizes:
   - `com.sap.sl.datasource.DataSource`
   - `com.businessobjects.mds.datafoundation.DataFoundation`
3. `javax.activation.DataSource` and unrelated classes are excluded.
4. The packaged runner was regenerated with the same behavior.

## Validation

- Javac notes/warnings/stderr/zero-exit/non-zero-exit test: passed.
- Focused Route B contract tests: **16 passed after the patch**.
- Full Python suite: **136 passed after the patch**.
- Ruff: clean.
- Mypy: clean across 38 source files.
- PowerShell syntax: passed.
- JSON parsing: passed.
- No SAP SDK runtime, CMS, HANA, or Milestone 2B execution performed.

