[CmdletBinding()]
param(
    [string]$JavaHome = $env:JAVA_HOME,
    [string]$SdkClasspath = $env:SAP_SDK_CLASSPATH
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$moduleRoot = Join-Path $repoRoot 'remote-sdk-extractor'
$targetRoot = Join-Path $moduleRoot 'target'
$classes = Join-Path $targetRoot 'classes'
$testClasses = Join-Path $targetRoot 'test-classes'

if ([string]::IsNullOrWhiteSpace($JavaHome)) {
    $JavaHome = (Get-Command javac -ErrorAction SilentlyContinue).Source | Split-Path -Parent | Split-Path -Parent
}
if ([string]::IsNullOrWhiteSpace($JavaHome) -or -not (Test-Path (Join-Path $JavaHome 'bin\javac.exe'))) {
    throw 'REQUIRED_INPUT: Java 11+ JDK not found. Set JAVA_HOME on the remote Windows machine.'
}

$javac = Join-Path $JavaHome 'bin\javac.exe'
New-Item -ItemType Directory -Force -Path $classes, $testClasses | Out-Null
$mainSources = @(Get-ChildItem (Join-Path $moduleRoot 'src\main\java') -Filter '*.java' -Recurse | ForEach-Object FullName)
$testSources = @(Get-ChildItem (Join-Path $moduleRoot 'src\test\java') -Filter '*.java' -Recurse | ForEach-Object FullName)

if ($mainSources.Count -eq 0) { throw 'No Java main sources found.' }
& $javac --release 11 -encoding UTF-8 -d $classes $mainSources
if ($LASTEXITCODE -ne 0) { throw "Java main compilation failed with exit code $LASTEXITCODE." }
if ($testSources.Count -gt 0) {
    & $javac --release 11 -encoding UTF-8 -cp $classes -d $testClasses $testSources
    if ($LASTEXITCODE -ne 0) { throw "Java test compilation failed with exit code $LASTEXITCODE." }
}
Write-Output "Compiled ROUTE_B_SDK skeleton to $targetRoot"
Write-Output "SAP SDK classpath supplied: $(-not [string]::IsNullOrWhiteSpace($SdkClasspath))"
