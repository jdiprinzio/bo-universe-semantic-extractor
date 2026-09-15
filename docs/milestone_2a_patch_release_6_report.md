# Milestone 2A Patch Release 6 Report

## JVM Discovery Fix

The native process helper now drains stdout and stderr asynchronously with
`ReadToEndAsync()`, waits for process completion, reads `Process.ExitCode`, and fails only when
that exit code is non-zero. This applies to both:

- `java.exe -version`
- `java.exe -XshowSettings:properties -version`

Informational stderr, including SAP JVM version/properties output, is accepted when exit code is
zero. The helper no longer depends on PowerShell native stderr stream behavior.

## Regression Coverage

`tests/powershell/test-milestone-2a-jvm-discovery.ps1` covers successful `java -version`,
successful `-XshowSettings:properties -version`, informational stderr with exit code zero, JVM
property capture, and non-zero failure propagation. Existing contract tests preserve classpath
inventory, exact candidate discovery, and capability validation assertions.

## Validation

- Focused Route B contract tests: **16 passed** after the patch.
- Full Python suite: **136 passed** after the patch.
- JVM discovery PowerShell regression: passed.
- Ruff: clean.
- Mypy: clean across 38 source files.
- PowerShell syntax: passed.
- JSON parsing: passed.
- No SAP SDK runtime, CMS, HANA, or Milestone 2B execution performed.
