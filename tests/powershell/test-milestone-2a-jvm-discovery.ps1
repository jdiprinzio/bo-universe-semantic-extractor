[CmdletBinding()]
param([string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path)

$ErrorActionPreference = 'Stop'
. (Join-Path $RepoRoot 'remote-sdk-extractor\scripts\invoke-informational-native.ps1')
$temp = Join-Path ([IO.Path]::GetTempPath()) ("route-b-jvm-test-" + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $temp | Out-Null
try {
    $javaVersion = Join-Path $temp 'java-version.ps1'
    'Write-Error ''java version "1.8.0_421"''; exit 0' | Set-Content -LiteralPath $javaVersion -Encoding UTF8
    $versionOutput = Invoke-InformationalNativeCommand -Executable (Get-Command powershell.exe).Source -Arguments @('-NoProfile', '-File', $javaVersion, '-version') -FailureCode 'JVM_DISCOVERY_FAILURE'
    if ($versionOutput -notmatch '1\.8\.0_421') { throw 'java -version output was not captured' }

    $properties = Join-Path $temp 'java-properties.ps1'
    "Write-Output 'java.vm.name = SAP JVM'; Write-Error 'java.vm.version = 1.8.0_421'; Write-Error 'sun.arch.data.model = 64'; exit 0" | Set-Content -LiteralPath $properties -Encoding UTF8
    $propertiesOutput = Invoke-InformationalNativeCommand -Executable (Get-Command powershell.exe).Source -Arguments @('-NoProfile', '-File', $properties, '-XshowSettings:properties', '-version') -FailureCode 'JVM_DISCOVERY_FAILURE'
    if ($propertiesOutput -notmatch 'sun.arch.data.model = 64') { throw 'JVM property output was not captured' }

    $failure = Join-Path $temp 'java-failure.ps1'
    'Write-Error "fatal JVM error"; exit 7' | Set-Content -LiteralPath $failure -Encoding UTF8
    try {
        Invoke-InformationalNativeCommand -Executable (Get-Command powershell.exe).Source -Arguments @('-NoProfile', '-File', $failure) -FailureCode 'JVM_DISCOVERY_FAILURE' | Out-Null
        throw 'non-zero JVM discovery exit did not fail'
    } catch {
        if ($_.Exception.Message -notmatch 'JVM_DISCOVERY_FAILURE') { throw }
    }

    Write-Output 'Milestone 2A JVM discovery tests passed'
} finally {
    Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
}
