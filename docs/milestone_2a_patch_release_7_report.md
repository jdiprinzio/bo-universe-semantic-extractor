# Milestone 2A Patch Release 7 Report

## JVM Discovery Fix

The native helper now returns structured `stdout`, `stderr`, and `exit_code` values after
asynchronously draining both streams and waiting for process completion. The runner serializes a
clean first non-empty JVM version line into `sdk_environment.json`; PowerShell exception-record
text is not used as the environment value.

JVM discovery progress is recorded in `discovery_progress.log` with start, completion,
environment-written, and candidate-discovered phases.

## Regression Coverage

- `java -version` informational stderr with exit code 0.
- `java -XshowSettings:properties -version` output capture.
- stdout/stderr preservation without PowerShell wrapper text.
- non-zero exit failure propagation.
- clean structured result output.

## Validation

- Focused Route B contract tests: **16 passed**.
- Full Python suite: **136 passed**.
- Dedicated clean JVM output test: passed.
- Ruff: clean.
- Mypy: clean across 38 source files.
- PowerShell syntax: passed.
- JSON parsing: passed.
- No SAP SDK runtime, CMS, HANA, or Milestone 2B execution performed.
