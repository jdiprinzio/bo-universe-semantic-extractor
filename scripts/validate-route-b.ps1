[CmdletBinding()]
param([string]$JavaHome = $env:JAVA_HOME)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
& (Join-Path $PSScriptRoot 'compile-route-b.ps1') -JavaHome $JavaHome
$moduleRoot = Join-Path $repoRoot 'remote-sdk-extractor'
$classes = Join-Path $moduleRoot 'target\classes'
$testClasses = Join-Path $moduleRoot 'target\test-classes'
$java = Join-Path $JavaHome 'bin\java.exe'
if (-not (Test-Path $java)) { $java = 'java.exe' }

& $java -cp "$classes;$testClasses" com.vistance.bo.routeb.RouteBContractTest
if ($LASTEXITCODE -ne 0) { throw "ROUTE_B Java contract tests failed with exit code $LASTEXITCODE." }
& $java -cp $classes com.vistance.bo.routeb.RouteBMain manifest
if ($LASTEXITCODE -ne 0) { throw "ROUTE_B manifest validation failed with exit code $LASTEXITCODE." }
Write-Output 'ROUTE_B local validation passed; no CMS connection attempted.'
