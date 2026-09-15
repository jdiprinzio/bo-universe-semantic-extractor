# Milestone 2A Patch Release 4 Report

## Fix

The runner previously invoked `javac.exe` directly while `$ErrorActionPreference = 'Stop'` was
active. Successful Java compilation can write notes/warnings to stderr, which PowerShell treated
as a terminating error even when javac returned exit code 0.

Compilation now uses the existing `Invoke-InformationalNativeCommand` helper. It captures stderr
as informational text, restores PowerShell error preferences, and fails only when `$LASTEXITCODE`
is non-zero. The packaged runner was regenerated with the same behavior.

## Regression Coverage

`tests/powershell/test-milestone-2a-javac-output.ps1` proves:

- javac-style notes on stderr with exit code 0 are accepted;
- javac-style warnings on stderr with exit code 0 are accepted;
- informational stderr with exit code 0 is accepted;
- non-zero compiler exit propagates `CLASSPATH_FAILURE`.

Python contract tests also verify the runner uses the helper and contains no direct javac call.

## Validation

- Focused Route B contract tests: **15 passed**.
- Full Python suite: **135 passed**.
- Native javac-output PowerShell test: passed.
- Ruff: clean.
- Mypy: clean across 38 source files.
- PowerShell syntax: passed.
- JSON parsing: passed.
- No SAP SDK runtime, CMS, or Milestone 2B execution performed.
