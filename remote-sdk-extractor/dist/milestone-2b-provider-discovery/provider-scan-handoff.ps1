<#
Shared provider-scan-to-probe handoff. Used identically by run-provider-discovery.ps1
(production) and simulate-provider-discovery.ps1 (local, Java-free) so both exercise the
same write/log/validate order. included_jars.json is written as human-readable evidence
only and is never read back or used to gate execution.
#>
function Invoke-ProviderScanHandoff {
    param(
        [Parameter(Mandatory=$true)][string]$OutputRoot,
        [Parameter(Mandatory=$true)]$ScanResult,
        [Parameter(Mandatory=$true)][string[]]$ConfirmedClasses,
        [Parameter(Mandatory=$true)][bool]$JavaToolsPresent,
        [Parameter(Mandatory=$true)][bool]$ProbeSourcePresent,
        [Parameter(Mandatory=$true)][scriptblock]$LogAction
    )
    # Step 1: authoritative line handoff, written before any validation can gate execution.
    $includedJarsTextPath=Join-Path $OutputRoot 'included_jars.txt'
    Write-Utf8NoBomLines $includedJarsTextPath @($ScanResult.IncludedJars|ForEach-Object{$_.absolute_path})
    & $LogAction "INCLUDED_JARS_WRITTEN path=$includedJarsTextPath"

    # Evidence only; never parsed, counted, or used to gate execution.
    $includedJarsJsonPath=Join-Path $OutputRoot 'included_jars.json'
    $ScanResult.IncludedJars|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $includedJarsJsonPath -Encoding UTF8

    # Step 2: confirmed classes handoff.
    $confirmedClassesPath=Join-Path $OutputRoot 'confirmed_classes.txt'
    Write-Utf8NoBomLines $confirmedClassesPath $ConfirmedClasses
    & $LogAction "CONFIRMED_CLASSES_WRITTEN path=$confirmedClassesPath"

    $ScanResult.Exclusions|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $OutputRoot 'provider_scan_exclusions.json') -Encoding UTF8

    # Step 3: preflight logging, always emitted before any mismatch check can throw.
    $handoffJarLines=@(Get-Content -LiteralPath $includedJarsTextPath -ErrorAction SilentlyContinue|Where-Object{($_.Trim()).Length -gt 0})
    & $LogAction "HANDOFF_PREFLIGHT included_jars_lines=$($handoffJarLines.Count) expected=$($ScanResult.Included)"
    & $LogAction "HANDOFF_PREFLIGHT confirmed_classes_lines=$($ConfirmedClasses.Count) expected=$($ConfirmedClasses.Count)"
    & $LogAction "HANDOFF_PREFLIGHT java_tools_present=$($JavaToolsPresent.ToString().ToLowerInvariant())"
    & $LogAction "HANDOFF_PREFLIGHT probe_source_present=$($ProbeSourcePresent.ToString().ToLowerInvariant())"

    # Step 4: validation, strictly after preflight logging.
    if($handoffJarLines.Count -ne $ScanResult.Included){throw "INCLUDED_JARS_LINE_COUNT_MISMATCH: expected=$($ScanResult.Included), actual=$($handoffJarLines.Count)"}
    $preflightFailures=New-Object System.Collections.ArrayList
    if($ConfirmedClasses.Count -eq 0){[void]$preflightFailures.Add('confirmed_classes_lines=0, expected>0')}
    if(-not $JavaToolsPresent){[void]$preflightFailures.Add('java_tools_present=false')}
    if(-not $ProbeSourcePresent){[void]$preflightFailures.Add('probe_source_present=false')}
    if($preflightFailures.Count -gt 0){throw "HANDOFF_PREFLIGHT_FAILURE: $($preflightFailures -join '; ')"}

    [pscustomobject]@{IncludedJarsTextPath=$includedJarsTextPath;ConfirmedClassesPath=$confirmedClassesPath}
}
