# Milestone 2A Portability Report

## Fixes

- Removed repository traversal from both source and packaged `run-milestone-2a.ps1` runners.
- The capability registry now resolves from `config\confirmed_sdk_capabilities.json` relative to the package root.
- The package includes its required capability registry, Java source, runner, and native-command helper.
- Added `-SelfTest`, which validates package dependencies and writes `self_test.json` without Java,
  SAP SDK, CMS, or universe inputs.
- Added automated assertions that fail on `..\`, external capability registry references, or
  missing package-local dependencies.

## Arbitrary-Directory Self-Test

Run from any current directory after copying the package:

```powershell
Set-Location C:\any\directory
C:\copied\milestone-2a\run-milestone-2a.ps1 -SelfTest -OutputDirectory C:\route-b-self-test
```

The self-test resolves all dependencies from the copied package root and writes
`C:\route-b-self-test\remote_discovery_output\self_test.json`.

## Validation

- Focused Route B contract tests: 12 passed.
- Full Python suite: 132 passed.
- Ruff: clean.
- Mypy: clean across 38 source files.
- Source and packaged PowerShell syntax: passed.
- JSON schema, capability registry, package manifest: parsed successfully.
- Package policy: passed; no SAP JARs, UNX/BLX/DFX/CNS files, credentials, or CMS sessions.
- SAP JVM/SDK runtime discovery: not executed in this local environment.
- CMS and HANA: not contacted.

## Remaining Boundary

The package is portable and ready to run on the remote BusinessObjects machine. Runtime discovery
still requires the remote SAP-supported JVM, SDK JARs, and six path inputs; this portability patch
does not begin SDK runtime discovery or Milestone 2B.
