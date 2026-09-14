[CmdletBinding()]
param(
    [ValidateSet('manifest', 'validate-classpath', 'export')]
    [string]$Command = 'manifest',
    [string]$JavaHome = $env:JAVA_HOME,
    [string]$SdkClasspath = $env:SAP_SDK_CLASSPATH
)

$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'compile-route-b.ps1') -JavaHome $JavaHome -SdkClasspath $SdkClasspath
$moduleRoot = Join-Path (Split-Path -Parent $PSScriptRoot) 'remote-sdk-extractor'
$classes = Join-Path $moduleRoot 'target\classes'
$java = Join-Path $JavaHome 'bin\java.exe'
if (-not (Test-Path $java)) { $java = 'java.exe' }

if ($Command -eq 'validate-classpath' -and [string]::IsNullOrWhiteSpace($SdkClasspath)) {
    throw 'REQUIRED_INPUT: SAP_SDK_CLASSPATH is not set. No SDK runtime test will be attempted.'
}
$env:SAP_SDK_CLASSPATH = $SdkClasspath
& $java -cp "$classes;$SdkClasspath" com.vistance.bo.routeb.RouteBMain $Command
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
