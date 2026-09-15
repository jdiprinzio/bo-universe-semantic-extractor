[CmdletBinding()]
param([string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path)

$ErrorActionPreference = 'Stop'
. (Join-Path $RepoRoot 'remote-sdk-extractor\scripts\invoke-informational-native.ps1')
$temp = Join-Path ([IO.Path]::GetTempPath()) ("route-b-clean-jvm-test-" + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $temp | Out-Null
try {
    $java = Join-Path $temp 'java.cmd'
    @'
@echo java.vm.name = SAP JVM
@echo java version "1.8.0_421" 1>&2
@echo sun.arch.data.model = 64 1>&2
@exit /b 0
'@ | Set-Content -LiteralPath $java -Encoding ASCII
    $result = Invoke-InformationalNativeCommand -Executable $java -Arguments @('-XshowSettings:properties', '-version') -FailureCode 'JVM_DISCOVERY_FAILURE'
    if ($result.exit_code -ne 0) { throw 'zero exit code was not preserved' }
    if ($result.stderr -notmatch '1\.8\.0_421') { throw 'stderr content was not preserved' }
    if ($result.stderr -match 'FullyQualifiedErrorId|NativeCommandError') { throw 'PowerShell exception text leaked into stderr result' }
    if ($result.stdout -notmatch 'SAP JVM') { throw 'stdout content was not preserved' }
    Write-Output 'Milestone 2A clean JVM output test passed'
} finally {
    Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
}
