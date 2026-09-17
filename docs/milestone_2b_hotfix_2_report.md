# Milestone 2B Hotfix 2 Report

## Verbatim defective code (original lines ~90-97)

```powershell
$includedJarsPath=Join-Path $script:OutputRoot 'included_jars.json'
$scanResult.IncludedJars|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $includedJarsPath -Encoding UTF8
$writtenIncludedJars=@(Get-Content -LiteralPath $includedJarsPath -Raw|ConvertFrom-Json)
if($writtenIncludedJars.Count -ne $scanResult.Included){throw "INCLUDED_JARS_WRITE_MISMATCH: expected=$($scanResult.Included), actual=$($writtenIncludedJars.Count)"}
$includedBytes=(Get-Item -LiteralPath $includedJarsPath).Length
PhaseLog "INCLUDED_JARS_WRITTEN count=$($writtenIncludedJars.Count) bytes=$includedBytes path=$includedJarsPath"
$includedJarsTextPath=Join-Path $script:OutputRoot 'included_jars.txt';Write-Utf8NoBomLines $includedJarsTextPath @($scanResult.IncludedJars|ForEach-Object{$_.absolute_path})
```

**This check validated `included_jars.json`** (the legacy JSON evidence file), not `included_jars.txt`. Because it ran before the `included_jars.txt` write and threw on mismatch, `included_jars.txt` was never created and `HANDOFF_PREFLIGHT`/`failure_diagnostics.json` never ran.

## Legacy code removed

The `ConvertTo-Json` → `ConvertFrom-Json` round-trip and its `INCLUDED_JARS_WRITE_MISMATCH` gate were deleted entirely. `included_jars.json` is now written once, as evidence only, and is never read back.

## Ordering correction

Extracted `Invoke-ProviderScanHandoff` into a new shared module, `provider-scan-handoff.ps1`, used identically by production and simulation. New order: write `included_jars.txt` → write `confirmed_classes.txt` (evidence JSON alongside, unread) → `HANDOFF_PREFLIGHT` logging → `INCLUDED_JARS_LINE_COUNT_MISMATCH`/`HANDOFF_PREFLIGHT_FAILURE` checks → probe invocation. A second defect was found and fixed during this work: the final `catch` block had silently lost its `Write-FailureDiagnostics` call, so `failure_diagnostics.json` was never written on **any** failure; the call is restored.

## Simulation and mutation test results

Simulation regenerates the real `PROVIDER_SCAN` filtering logic (not a hand-picked list) and now defaults to 152 provider JARs + 20 excluded, calling the same shared handoff function as production: `total=172 included=152 excluded=20`, `SIMULATION_PASSED`.

Mutation test: reintroduced the legacy JSON gate in a temp copy of the shared module. Result: **failed** with `INCLUDED_JARS_WRITE_MISMATCH: expected=152, actual=1`, reproducing the exact production symptom. Restoring the unmutated module: **passed** (`SIMULATION_PASSED`).

## Validation results

- Focused Route B contracts: `60 passed`.
- Full repository suite: `180 passed`.
- Ruff: `All checks passed!`.
- Mypy: `7 errors`, all pre-existing and unrelated (`test_query_panel_outline_parser.py`, `test_bo_rest_contract.py`, `test_cli_contract.py`); zero errors in Route B files.

## Report path

`docs/milestone_2b_hotfix_2_report.md`
