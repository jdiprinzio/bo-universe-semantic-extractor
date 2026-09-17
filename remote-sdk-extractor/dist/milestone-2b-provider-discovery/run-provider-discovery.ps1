[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SapInstallRoot,
    [Parameter(Mandatory=$true)][string]$IdtPluginDirectory,
    [Parameter(Mandatory=$true)][string]$SapJvmBinDirectory,
    [Parameter(Mandatory=$true)][string]$WorkingDirectory,
    [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference='Stop'
$script:PackageRoot = if(Test-Path (Join-Path $PSScriptRoot 'config\confirmed_sdk_capabilities.json')){$PSScriptRoot}else{Split-Path -Parent $PSScriptRoot}
. (Join-Path $script:PackageRoot 'invoke-informational-native.ps1')

function Require([string]$Path,[string]$Code){if(-not(Test-Path -LiteralPath $Path)){throw "$Code`: missing path $Path"}}

Require $SapInstallRoot 'MISSING_SAP_INSTALL_ROOT'
Require $IdtPluginDirectory 'MISSING_IDT_PLUGIN_DIRECTORY'
Require $SapJvmBinDirectory 'MISSING_SAP_JVM_DIRECTORY'
Require $WorkingDirectory 'MISSING_WORKING_DIRECTORY'
$tools=@{}
foreach($name in @('java.exe','javac.exe')){
    $path=Join-Path $SapJvmBinDirectory $name
    Require $path 'MISSING_JAVA_TOOL'
    $tools[$name]=$path
}
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

# Compile only; PowerShell performs no discovery, filtering, or reflection of its own.
$javaSourceRoot = Join-Path $script:PackageRoot 'src\main\java'
$classes = Join-Path $WorkingDirectory 'provider-classes'
New-Item -ItemType Directory -Force -Path $classes | Out-Null
$sources = @(Get-ChildItem -LiteralPath $javaSourceRoot -Filter '*.java' -File -Recurse | ForEach-Object FullName)
Invoke-InformationalNativeCommand $tools['javac.exe'] (@('-encoding','UTF8','-d',$classes)+$sources) 'JAVA_COMPILATION_FAILURE' | Out-Null

# Java owns discovery, filtering, class enumeration, reflection, progress logging, and diagnostics.
$result = Invoke-InformationalNativeCommand $tools['java.exe'] @('-Xmx4g','-cp',$classes,'com.vistance.bo.routeb.ProviderDiscoveryProbe',$SapInstallRoot,$IdtPluginDirectory,$OutputDirectory) 'PROVIDER_DISCOVERY_FAILURE'
Write-Output $result.stdout
if ($result.stderr) { Write-Output $result.stderr }
