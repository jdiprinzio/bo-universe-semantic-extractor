# Milestone 2A Patch Report

## Patch

The remote runner previously invoked `java -version` while `$ErrorActionPreference = 'Stop'` was
active. Java writes version information to stderr even on success, so PowerShell treated the
informational stream as an exception and stopped before capability validation.

The patch moves native informational execution into the tested
`remote-sdk-extractor/scripts/invoke-informational-native.ps1` helper. The helper temporarily sets
`ErrorActionPreference` to `Continue`, captures stdout/stderr as text, restores the previous
preference in `finally`, and throws only when `$LASTEXITCODE` is non-zero. JVM property discovery
uses the same path. The packaged runner includes the helper.

Existing classpath inventory, capability validation, `javap`, reflection-only probing, output
hashing, security controls, and CMS-disconnected behavior are unchanged.

## Modified Files

- `remote-sdk-extractor/scripts/run-milestone-2a.ps1`
- `remote-sdk-extractor/scripts/invoke-informational-native.ps1`
- `remote-sdk-extractor/dist/milestone-2a/run-milestone-2a.ps1`
- `remote-sdk-extractor/dist/milestone-2a/invoke-informational-native.ps1`
- `tests/powershell/test-milestone-2a-native.ps1`
- `tests/contract/test_route_b_milestone_1_contract.py`
- `docs/milestone_2a_patch_report.md`

## Automated Coverage

- Successful stderr-only native output is accepted.
- Non-zero native exit code produces `JVM_DISCOVERY_FAILURE`.
- Existing tests assert classpath generation, capability registry use, and probe execution.

## Validation

- Focused Route B tests: 11 passed after the patch.
- Full Python suite: 131 passed after the patch.
- Ruff: clean.
- Mypy: clean across 38 source files.
- PowerShell syntax: source runner, packaged runner, helper, and native-command test parsed.
- Java/CMS runtime: not executed locally; no Java or SAP SDK runtime is installed here.

## Exact Remote Rerun

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
Set-Location C:\path\to\bo-universe-semantic-extractor
.\remote-sdk-extractor\scripts\run-milestone-2a.ps1 `
  -SapInstallRoot 'C:\Program Files\SAP BusinessObjects' `
  -IdtPluginDirectory 'C:\Program Files\SAP BusinessObjects\Information Design Tool\plugins' `
  -SapJvmBinDirectory 'C:\path\to\sap-supported-jvm\bin' `
  -LocalIdtProjectDirectory 'C:\IDT\workspace' `
  -WorkingDirectory 'C:\route-b-work' `
  -OutputDirectory 'C:\route-b-output'
```

The expected successful execution report proceeds beyond JVM discovery to classpath inventory,
capability validation, and reflection-only loading-bridge discovery. CMS remains disconnected.
