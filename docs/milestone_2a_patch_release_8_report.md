# Milestone 2A Patch Release 8 Report

## Fix

The runner now wraps long-running discovery operations in `Invoke-Phase`, which:

- logs `START`, `HEARTBEAT`, `COMPLETE`, `FAILURE`, and `TIMEOUT` markers;
- emits a heartbeat every 30 seconds;
- uses a configurable `PhaseTimeoutSeconds` value (default 900 seconds);
- stops timed-out jobs and raises a structured `PHASE_TIMEOUT` failure.

Bounded phases now cover JAR inventory, JAR metadata/hash generation, exact candidate discovery,
and javap discovery. The existing JVM discovery progress markers remain intact. This prevents the
post-`SDK_ENVIRONMENT_WRITTEN` hang from remaining silent and ensures the runner either completes
or returns a structured failure.

## Validation

- Focused Route B contract tests: **16 passed** after the patch.
- Full Python suite: **136 passed** after the patch.
- Ruff: clean.
- Mypy: clean across 38 source files.
- PowerShell syntax: passed.
- JSON parsing: passed.
- No SAP SDK runtime, CMS, HANA, or Milestone 2B execution performed.
