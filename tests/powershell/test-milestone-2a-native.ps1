[CmdletBinding()]
param([string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path)

$ErrorActionPreference = 'Stop'
. (Join-Path $RepoRoot 'remote-sdk-extractor\scripts\invoke-informational-native.ps1')
$temp = Join-Path ([IO.Path]::GetTempPath()) ("route-b-native-test-" + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $temp | Out-Null
try {
    $success = Join-Path $temp 'success.cmd'
    "@echo java version `"1.8.0_421`" 1>&2`r`n@exit /b 0" | Set-Content -LiteralPath $success -Encoding ASCII
    $output = Invoke-InformationalNativeCommand -Executable $success -Arguments @() -FailureCode 'JVM_DISCOVERY_FAILURE'
    if ($output -notmatch '1\.8\.0_421') { throw 'successful stderr output was not captured' }

    $failure = Join-Path $temp 'failure.cmd'
    "@echo broken java 1>&2`r`n@exit /b 7" | Set-Content -LiteralPath $failure -Encoding ASCII
    try {
        Invoke-InformationalNativeCommand -Executable $failure -Arguments @() -FailureCode 'JVM_DISCOVERY_FAILURE' | Out-Null
        throw 'non-zero native exit did not fail'
    } catch {
        if ($_.Exception.Message -notmatch 'JVM_DISCOVERY_FAILURE') { throw }
    }

    Write-Output 'Milestone 2A native-command tests passed'
} finally {
    Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
}
