[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [int]$ProviderJarCount = 152,
    [int]$ExcludedJarCount = 20
)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.IO.Compression
New-Item -ItemType Directory -Force -Path $OutputDirectory|Out-Null
. (Join-Path $PSScriptRoot 'provider-scan-handoff.ps1')
function Write-Utf8NoBomLines([string]$Path,[string[]]$Lines){[IO.File]::WriteAllLines($Path,$Lines,(New-Object Text.UTF8Encoding($false)))}
function PhaseLog([string]$Value){Write-Output $Value}

$source=Join-Path $OutputDirectory 'synthetic-jars';New-Item -ItemType Directory -Force -Path $source|Out-Null
function New-SyntheticJar([string]$Name,[string[]]$Entries){
    $path=Join-Path $source $Name
    $archive=[IO.Compression.ZipFile]::Open($path,[IO.Compression.ZipArchiveMode]::Create)
    try{foreach($entryName in $Entries){$entry=$archive.CreateEntry($entryName);$stream=$entry.Open();$stream.Dispose()}}finally{$archive.Dispose()}
    return Get-Item -LiteralPath $path
}

# Reproduce production's PROVIDER_SCAN filtering rather than a hand-picked pass/fail list,
# so this exercises the identical handoff code path at production scale.
$providerJarPrefixes=@('com.sap.sl.','com.businessobjects.mds.','com.businessobjects.dsl.','com.businessobjects.sdk.','com.businessobjects.boesdk')
$knownNames=@('cesdk.jar','cecore.jar','celib.jar','cesession.jar')
$irrelevant=@('eclipse','localization','jetty','batik','lucene','poi','axis2','visualization','help','language')

$jars=New-Object System.Collections.ArrayList
for($i=0;$i -lt $ProviderJarCount;$i++){[void]$jars.Add((New-SyntheticJar "com.sap.sl.synthetic$i.jar" @("com/sap/sl/synthetic/Type$i.class")))}
for($i=0;$i -lt $ExcludedJarCount;$i++){[void]$jars.Add((New-SyntheticJar "jetty-synthetic-$i.jar" @("org/eclipse/jetty/Synthetic$i.class")))}
$jars=@($jars)

$includedJars=New-Object System.Collections.ArrayList;$exclusions=New-Object System.Collections.ArrayList
foreach($jar in $jars){
    $lowerName=$jar.Name.ToLowerInvariant()
    $selected=($knownNames -contains $lowerName) -or (($providerJarPrefixes|Where-Object{$lowerName.StartsWith($_)}).Count -gt 0)
    if(-not $selected){
        $reason='jar name does not match a provider runtime family'
        $matched=$irrelevant|Where-Object{$lowerName.Contains($_)}|Select-Object -First 1
        if($matched){$reason="excluded irrelevant bundle family: $matched"}
        [void]$exclusions.Add([ordered]@{file_name=$jar.Name;absolute_path=$jar.FullName;reason=$reason})
    }else{[void]$includedJars.Add([ordered]@{file_name=$jar.Name;absolute_path=$jar.FullName})}
}
$scanResult=[pscustomobject]@{IncludedJars=@($includedJars);Exclusions=@($exclusions);Total=$jars.Count;Included=$includedJars.Count;Excluded=$exclusions.Count}
if($scanResult.Included -lt 152){throw "SIMULATION_SCALE_FAILURE: included=$($scanResult.Included), expected>=152"}
PhaseLog "PROVIDER_SCAN FILTERED total=$($scanResult.Total) included=$($scanResult.Included) excluded=$($scanResult.Excluded)"

$confirmedClasses=@('com.sap.sl.datasource.DataSource','com.businessobjects.mds.datafoundation.DataFoundation')
$handoff=Invoke-ProviderScanHandoff -OutputRoot $OutputDirectory -ScanResult $scanResult -ConfirmedClasses $confirmedClasses -JavaToolsPresent $true -ProbeSourcePresent $true -LogAction ${function:PhaseLog}

$includedLines=@(Get-Content -LiteralPath $handoff.IncludedJarsTextPath|Where-Object{($_.Trim()).Length -gt 0})
$confirmedLines=@(Get-Content -LiteralPath $handoff.ConfirmedClassesPath|Where-Object{($_.Trim()).Length -gt 0})
if($includedLines.Count -ne $scanResult.Included){throw "SIMULATION_HANDOFF_FAILURE: included_jars_lines=$($includedLines.Count), expected=$($scanResult.Included)"}
if($confirmedLines.Count -ne $confirmedClasses.Count){throw "SIMULATION_HANDOFF_FAILURE: confirmed_classes_lines=$($confirmedLines.Count), expected=$($confirmedClasses.Count)"}

[ordered]@{status='SIMULATION_PASSED';total_jars=$jars.Count;included_jars=$scanResult.Included;excluded_jars=$scanResult.Excluded;included_jars_lines=$includedLines.Count;confirmed_classes_lines=$confirmedLines.Count}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $OutputDirectory 'simulation_result.json') -Encoding UTF8
Write-Output 'SIMULATION_PASSED'
