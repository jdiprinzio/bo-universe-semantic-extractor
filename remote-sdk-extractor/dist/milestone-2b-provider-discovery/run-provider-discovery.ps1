[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SapInstallRoot,
    [Parameter(Mandatory=$true)][string]$IdtPluginDirectory,
    [Parameter(Mandatory=$true)][string]$SapJvmBinDirectory,
    [Parameter(Mandatory=$true)][string]$LocalIdtProjectDirectory,
    [Parameter(Mandatory=$true)][string]$WorkingDirectory,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [int]$PhaseTimeoutSeconds = 3600
)
$ErrorActionPreference='Stop'
$script:PackageRoot = if(Test-Path (Join-Path $PSScriptRoot 'config\confirmed_sdk_capabilities.json')){$PSScriptRoot}else{Split-Path -Parent $PSScriptRoot}
$script:OutputRoot=Join-Path $OutputDirectory 'provider_discovery'
. (Join-Path $script:PackageRoot 'invoke-informational-native.ps1')
. (Join-Path $script:PackageRoot 'provider-scan-handoff.ps1')
$script:ProgressLog=Join-Path $script:OutputRoot 'discovery_progress.log'
function PhaseLog([string]$Value){New-Item -ItemType Directory -Force -Path $script:OutputRoot|Out-Null;Add-Content -LiteralPath $script:ProgressLog -Value (([DateTime]::UtcNow.ToString('o'))+' '+$Value)}
function Phase([string]$Name,[scriptblock]$Action){
    PhaseLog "$Name START"
    $job=Start-Job -ScriptBlock $Action
    $deadline=[DateTime]::UtcNow.AddSeconds($PhaseTimeoutSeconds)
    $received=New-Object System.Collections.ArrayList
    try{
        while($job.State -eq 'Running'){
            foreach($item in @(Receive-Job -Job $job -ErrorAction Stop)){
                if($item -and $item.kind -eq 'heartbeat'){
                    PhaseLog $item.message
                }elseif($item -is [string] -and $item.StartsWith('PROBE_SCOPE HEARTBEAT')){
                    PhaseLog $item
                }else{[void]$received.Add($item)}
            }
            if([DateTime]::UtcNow -ge $deadline){
                Stop-Job -Job $job -ErrorAction SilentlyContinue
                PhaseLog "$Name FAILURE TIMEOUT"
                throw "PHASE_TIMEOUT: $Name"
            }
            Start-Sleep -Seconds 30
        }
        if($job.State -ne 'Completed'){PhaseLog "$Name FAILURE $($job.State)";throw "PHASE_FAILURE: $Name"}
        foreach($item in @(Receive-Job -Job $job -ErrorAction Stop)){
            if($item -and $item.kind -eq 'heartbeat'){
                PhaseLog $item.message
            }elseif($item -is [string] -and $item.StartsWith('PROBE_SCOPE HEARTBEAT')){
                PhaseLog $item
            }else{[void]$received.Add($item)}
        }
        PhaseLog "$Name COMPLETE"
        return @($received)
    }finally{Remove-Job -Job $job -Force -ErrorAction SilentlyContinue}
}
function Require([string]$Path,[string]$Code){if(-not(Test-Path -LiteralPath $Path)){throw "$Code`: missing path $Path"}}
function Write-Utf8NoBomLines([string]$Path,[string[]]$Lines){[IO.File]::WriteAllLines($Path,$Lines,(New-Object Text.UTF8Encoding($false)))}
function Write-FailureDiagnostics([string]$Code,[string]$Message){
    $files=@('included_jars.txt','included_jars.json','confirmed_classes.txt','provider_discovery_findings.json');$handoffs=[ordered]@{}
    foreach($name in $files){$path=Join-Path $script:OutputRoot $name;$lines=@();$bytes=0;if(Test-Path -LiteralPath $path){$bytes=(Get-Item -LiteralPath $path).Length;$lines=@(Get-Content -LiteralPath $path|Where-Object{($_.Trim()).Length -gt 0})};$handoffs[$name]=[ordered]@{bytes=$bytes;line_count=$lines.Count}}
    $scope=@{};$findingsPath=Join-Path $script:OutputRoot 'provider_discovery_findings.json';if(Test-Path -LiteralPath $findingsPath){try{$findingDocument=@(Get-Content -LiteralPath $findingsPath -Raw|ConvertFrom-Json)|Select-Object -First 1;if($findingDocument.scope){$scope=$findingDocument.scope}}catch{}}
    [ordered]@{phase='PROVIDER_DISCOVERY';error_code=$Code;message=$Message;handoff_files=$handoffs;probe_scope=$scope;java_tools=$tools;java_version=$script:JavaVersion;last_progress_lines=@(Get-Content -LiteralPath $script:ProgressLog -ErrorAction SilentlyContinue|Select-Object -Last 20)}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $script:OutputRoot 'failure_diagnostics.json') -Encoding UTF8
}
try{
    PhaseLog 'START'
    Require $SapInstallRoot 'MISSING_SAP_INSTALL_ROOT';Require $IdtPluginDirectory 'MISSING_IDT_PLUGIN_DIRECTORY';Require $SapJvmBinDirectory 'MISSING_SAP_JVM_DIRECTORY';Require $LocalIdtProjectDirectory 'MISSING_IDT_PROJECT_DIRECTORY';Require $WorkingDirectory 'MISSING_WORKING_DIRECTORY'
    New-Item -ItemType Directory -Force -Path $script:OutputRoot|Out-Null
    $tools=@{};foreach($name in @('java.exe','javac.exe','javap.exe')){$path=Join-Path $SapJvmBinDirectory $name;Require $path 'MISSING_JAVA_TOOL';$tools[$name]=$path}
    $jars=@(Phase 'JAR_INVENTORY' {@(Get-ChildItem -LiteralPath $using:SapInstallRoot -Filter '*.jar' -File -Recurse;Get-ChildItem -LiteralPath $using:IdtPluginDirectory -Filter '*.jar' -File -Recurse)|Sort-Object FullName -Unique});if($jars.Count -eq 0){throw 'MISSING_SDK_JARS: no SDK jars'}
    $jars|ForEach-Object{[ordered]@{file_name=$_.Name;absolute_path=$_.FullName;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash;copied_into_package=$false}}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $script:OutputRoot 'sdk_jar_inventory.json') -Encoding UTF8
    $registry=Get-Content -LiteralPath (Join-Path $script:PackageRoot 'config\confirmed_sdk_capabilities.json') -Raw|ConvertFrom-Json
    $confirmedClasses=@($registry.capabilities|ForEach-Object{$_.class}|Where-Object{$_})
    $classpath=$jars.FullName -join [IO.Path]::PathSeparator;Set-Content -LiteralPath (Join-Path $script:OutputRoot 'runtime_classpath.txt') -Value $classpath -Encoding UTF8
    $java=Invoke-InformationalNativeCommand $tools['java.exe'] @('-version') 'JVM_DISCOVERY_FAILURE';$props=Invoke-InformationalNativeCommand $tools['java.exe'] @('-XshowSettings:properties','-version') 'JVM_DISCOVERY_FAILURE'
    $script:JavaVersion=(($java.stdout+$java.stderr -split "`r?`n"|Where-Object{$_.Trim()}|Select-Object -First 1) -join '').Trim()
    [ordered]@{java_version=($java.stdout+$java.stderr -split "`r?`n"|Where-Object{$_.Trim()}|Select-Object -First 1);jvm_properties=$props.stdout+$props.stderr;cms_connection_attempted=$false}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $script:OutputRoot 'sdk_environment.json') -Encoding UTF8
    $scan=Phase 'PROVIDER_SCAN' {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $providerJarPrefixes=@('com.sap.sl.','com.businessobjects.mds.','com.businessobjects.dsl.','com.businessobjects.sdk.','com.businessobjects.boesdk')
        $knownNames=@('cesdk.jar','cecore.jar','celib.jar','cesession.jar')
        $irrelevant=@('eclipse','localization','jetty','batik','lucene','poi','axis2','visualization','help','language')
        $includedJars=New-Object System.Collections.ArrayList;$exclusions=New-Object System.Collections.ArrayList;$scanned=0;$total=$using:jars.Count;$nextHeartbeat=[DateTime]::UtcNow.AddSeconds(30)
        foreach($jar in $using:jars){
            $scanned++
            $lowerName=$jar.Name.ToLowerInvariant();$selected=($knownNames -contains $lowerName) -or (($providerJarPrefixes|Where-Object{$lowerName.StartsWith($_)}).Count -gt 0)
            if(-not $selected){$reason='jar name does not match a provider runtime family';$matched=$irrelevant|Where-Object{$lowerName.Contains($_)}|Select-Object -First 1;if($matched){$reason="excluded irrelevant bundle family: $matched"};[void]$exclusions.Add([ordered]@{file_name=$jar.Name;absolute_path=$jar.FullName;reason=$reason})}
            if($selected){[void]$includedJars.Add([ordered]@{file_name=$jar.Name;absolute_path=$jar.FullName})}
            if([DateTime]::UtcNow -ge $nextHeartbeat){[pscustomobject]@{kind='heartbeat';message="PROVIDER_SCAN HEARTBEAT scanned=$scanned of $total"};$nextHeartbeat=[DateTime]::UtcNow.AddSeconds(30)}
        }
        [pscustomobject]@{kind='scan-result';IncludedJars=@($includedJars);Exclusions=@($exclusions);Total=$total;Included=$includedJars.Count;Excluded=$exclusions.Count}
    }
    $scanResult=@(@($scan|Where-Object {$_.kind -eq 'scan-result'})|Select-Object -First 1)
    if($null -eq $scanResult){throw 'PROVIDER_SCAN_FAILURE: no scan result returned'}
    if($scanResult.Included -ge $scanResult.Total){throw 'PROVIDER_SCAN_FILTER_FAILURE: filtering did not reduce the scan set'}
    PhaseLog "PROVIDER_SCAN FILTERED total=$($scanResult.Total) included=$($scanResult.Included) excluded=$($scanResult.Excluded)"
    $javaToolsPresent=[bool]($tools['java.exe'] -and $tools['javac.exe'] -and $tools['javap.exe']);$probeSourcePresent=[bool](Test-Path (Join-Path $script:PackageRoot 'src\main\java\com\vistance\bo\routeb\ProviderDiscoveryProbe.java'))
    $handoff=Invoke-ProviderScanHandoff -OutputRoot $script:OutputRoot -ScanResult $scanResult -ConfirmedClasses $confirmedClasses -JavaToolsPresent $javaToolsPresent -ProbeSourcePresent $probeSourcePresent -LogAction ${function:PhaseLog}
    $includedJarsTextPath=$handoff.IncludedJarsTextPath
    $root=Join-Path $script:PackageRoot 'src\main\java';$classes=Join-Path $WorkingDirectory 'provider-classes';New-Item -ItemType Directory -Force -Path $classes|Out-Null;$sources=@(Get-ChildItem -LiteralPath $root -Filter '*.java' -File -Recurse|ForEach-Object FullName);Invoke-InformationalNativeCommand $tools['javac.exe'] (@('-encoding','UTF8','-d',$classes)+$sources) 'CLASSPATH_FAILURE'|Out-Null
    $probeOutputRoot=$script:OutputRoot;$javaTool=$tools['java.exe'];$probeClasspath=(($classes)+[IO.Path]::PathSeparator+(($jars.DirectoryName|Sort-Object -Unique|ForEach-Object{Join-Path $_ '*'})-join [IO.Path]::PathSeparator))
    Phase 'LOADER_CANDIDATE_ANALYSIS' {& $using:javaTool -cp $using:probeClasspath com.vistance.bo.routeb.ProviderDiscoveryProbe $using:includedJarsTextPath $using:probeOutputRoot (Join-Path $using:script:OutputRoot 'confirmed_classes.txt')}|Out-Null
    $findings=@(@(Get-Content -LiteralPath (Join-Path $script:OutputRoot 'provider_discovery_findings.json') -Raw|ConvertFrom-Json)|Select-Object -First 1)
    if([int]$findings.scope.jars -ne [int]$scanResult.Included){throw "PROBE_SCOPE_MISMATCH: filtered included=$($scanResult.Included), probe jars=$($findings.scope.jars)"}
    if(([double]$findings.scope.classes_enumerated / [double]$findings.scope.jars) -lt 10){throw "PROBE_SCOPE_MISMATCH: classes_enumerated=$($findings.scope.classes_enumerated), jars=$($findings.scope.jars)"}
    PhaseLog "PROBE_SCOPE jars=$($findings.scope.jars)"
    PhaseLog "PROBE_SCOPE classes_enumerated=$($findings.scope.classes_enumerated)"
    PhaseLog "PROBE_SCOPE classes_loaded=$($findings.scope.classes_loaded)"
    PhaseLog "PROBE_SCOPE classes_skipped=$($findings.scope.classes_skipped)"
    PhaseLog "PROBE_SCOPE methods_inspected=$($findings.scope.methods_inspected)"
    $hashes=Get-ChildItem -LiteralPath $script:OutputRoot -File|Where-Object Name -ne 'hashes.sha256'|Sort-Object Name|ForEach-Object{$hash=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash;"$hash  $($_.Name)"};Set-Content -LiteralPath (Join-Path $script:OutputRoot 'hashes.sha256') -Value $hashes -Encoding UTF8
    "# Milestone 2B Execution Report`n`n- Status: PROVIDER_DISCOVERY_COMPLETE`n- CMS connection attempted: false`n- Provider scan total: $($scanResult.Total)`n- Provider scan included: $($scanResult.Included)`n- Provider scan excluded: $($scanResult.Excluded)`n- Provider scan: JAR filtering; Java probe owns class enumeration`n"|Set-Content -LiteralPath (Join-Path $script:OutputRoot 'execution_report.md') -Encoding UTF8
}catch{$message=$_.Exception.Message;PhaseLog "FAILURE $message";Write-FailureDiagnostics 'PROVIDER_DISCOVERY_FAILURE' $message;throw}
