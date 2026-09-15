# Milestone 2A Patch Release 9 Report

## Java 8 Strategy

The SAP Java 8 launcher no longer receives an `@argument-file`. The probe now uses a compact,
Java 8-compatible classpath composed of:

1. the temporary compiled probe directory; and
2. one wildcard classpath entry per unique external SDK JAR directory.

The full raw runtime classpath remains in `runtime_classpath.txt` for evidence. SAP JARs are not
copied into the repository or package. The per-JAR `javap` strategy is unchanged.

## Validation

- Focused Route B contract tests: **16 passed** after the patch.
- Full Python suite: **136 passed** after the patch.
- Ruff: clean.
- Mypy: clean across 38 source files.
- PowerShell syntax: passed.
- JSON parsing: passed.
- No SAP SDK runtime, CMS, HANA, or Milestone 2B execution performed.
