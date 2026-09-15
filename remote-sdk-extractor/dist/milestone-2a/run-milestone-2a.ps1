[CmdletBinding()]
param(
    [string]$SapInstallRoot,
    [string]$IdtPluginDirectory,
    [string]$SapJvmBinDirectory,
    [string]$LocalIdtProjectDirectory,
    [string]$WorkingDirectory,
    [string]$OutputDirectory,
    [string]$CapabilityRegistry,
    [switch]$SelfTest,
    [int]$PhaseTimeoutSeconds = 900
)

$ErrorActionPreference = 'Stop'
$script:PackageRoot = if (Test-Path (Join-Path $PSScriptRoot 'config\confirmed_sdk_capabilities.json')) {
    $PSScriptRoot
} else {
    Split-Path -Parent $PSScriptRoot
}
$script:OutputRoot = if ($OutputDirectory) { Join-Path $OutputDirectory 'remote_discovery_output' } else { Join-Path $script:PackageRoot 'remote_discovery_output' }
$script:CapabilityRegistry = if ($CapabilityRegistry) { $CapabilityRegistry } else { Join-Path $script:PackageRoot 'config\confirmed_sdk_capabilities.json' }
. (Join-Path $script:PackageRoot 'invoke-informational-native.ps1')
$script:ProgressLog = Join-Path $script:OutputRoot 'discovery_progress.log'

function Write-ProgressPhase {
    param([string]$Phase)
    New-Item -ItemType Directory -Force -Path $script:OutputRoot | Out-Null
    Add-Content -LiteralPath $script:ProgressLog -Value ("{0} {1}" -f [DateTime]::UtcNow.ToString('o'), $Phase) -Encoding UTF8
}

function Invoke-Phase {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Action,
        [int]$TimeoutSeconds = $PhaseTimeoutSeconds
    )
    Write-ProgressPhase "$Name START"
    $job = Start-Job -ScriptBlock $Action
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    try {
        while ($job.State -eq 'Running') {
            if ([DateTime]::UtcNow -ge $deadline) {
                Stop-Job -Job $job -Force -ErrorAction SilentlyContinue
                Write-ProgressPhase "$Name FAILURE TIMEOUT"
                throw "PHASE_TIMEOUT: $Name exceeded $TimeoutSeconds seconds"
            }
            Start-Sleep -Seconds 30
            Write-ProgressPhase "$Name HEARTBEAT"
        }
        if ($job.State -ne 'Completed') {
            $reason = if ($job.ChildJobs[0].JobStateInfo.Reason) { $job.ChildJobs[0].JobStateInfo.Reason.Message } else { $job.State }
            Write-ProgressPhase "$Name FAILURE $reason"
            throw "PHASE_FAILURE: $Name failed: $reason"
        }
        $result = Receive-Job -Job $job -ErrorAction Stop
        Write-ProgressPhase "$Name COMPLETE"
        return $result
    } catch {
        if ($_.Exception.Message -notmatch "^PHASE_TIMEOUT:|^PHASE_FAILURE:") { Write-ProgressPhase "$Name FAILURE $($_.Exception.Message)" }
        throw
    } finally {
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }
}

function Write-Failure {
    param([string]$Code, [string]$Message)
    New-Item -ItemType Directory -Force -Path $script:OutputRoot | Out-Null
    $failure = [ordered]@{
        schema_version = 'route_b.sdk.v1'
        status = 'FAILED'
        error_code = $Code
        message = $Message
        cms_connection_attempted = $false
        generated_at_utc = [DateTime]::UtcNow.ToString('o')
    }
    $failure | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $script:OutputRoot 'loading_bridge_findings.json') -Encoding UTF8
    "# Milestone 2A Execution Report`n`n- Status: FAILED`n- Error code: $Code`n- Message: $Message`n- CMS connection attempted: false`n" | Set-Content -LiteralPath (Join-Path $script:OutputRoot 'execution_report.md') -Encoding UTF8
}

function Require-Path {
    param([string]$PathValue, [string]$Code, [string]$Label)
    if (-not (Test-Path -LiteralPath $PathValue)) {
        throw "$Code`: $Label does not exist: $PathValue"
    }
}

function Invoke-SelfTest {
    $required = @(
        (Join-Path $script:PackageRoot 'config\confirmed_sdk_capabilities.json'),
        (Join-Path $script:PackageRoot 'invoke-informational-native.ps1'),
        (Join-Path $script:PackageRoot 'src\main\java\com\vistance\bo\routeb\Milestone2aProbe.java')
    )
    foreach ($path in $required) { Require-Path $path 'PACKAGE_SELF_TEST_FAILURE' 'package dependency' }
    $registry = Get-Content -LiteralPath (Join-Path $script:PackageRoot 'config\confirmed_sdk_capabilities.json') -Raw | ConvertFrom-Json
    if ($registry.capability_status -ne 'CONFIRMED_BY_JAVAP') { throw 'PACKAGE_SELF_TEST_FAILURE: capability registry is malformed' }
    New-Item -ItemType Directory -Force -Path $script:OutputRoot | Out-Null
    [ordered]@{ status = 'PACKAGE_SELF_TEST_PASSED'; package_root = $script:PackageRoot; cms_connection_attempted = $false; capability_registry = 'config\confirmed_sdk_capabilities.json' } |
        ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $script:OutputRoot 'self_test.json') -Encoding UTF8
    Write-Output "Milestone 2A package self-test passed: $script:PackageRoot"
}

try {
    if ($SelfTest) { Invoke-SelfTest; return }
    Write-ProgressPhase 'START'
    foreach ($requiredInput in @(
        @{ Value = $SapInstallRoot; Code = 'MISSING_SAP_INSTALL_ROOT'; Label = 'SAP install root' },
        @{ Value = $IdtPluginDirectory; Code = 'MISSING_IDT_PLUGIN_DIRECTORY'; Label = 'IDT plugin directory' },
        @{ Value = $SapJvmBinDirectory; Code = 'MISSING_SAP_JVM_DIRECTORY'; Label = 'SAP JVM bin directory' },
        @{ Value = $LocalIdtProjectDirectory; Code = 'MISSING_IDT_PROJECT_DIRECTORY'; Label = 'local IDT project directory' },
        @{ Value = $WorkingDirectory; Code = 'MISSING_WORKING_DIRECTORY'; Label = 'working directory' },
        @{ Value = $OutputDirectory; Code = 'MISSING_OUTPUT_DIRECTORY'; Label = 'output directory' }
    )) {
        if ([string]::IsNullOrWhiteSpace($requiredInput.Value)) { throw "$($requiredInput.Code): $($requiredInput.Label) was not supplied" }
    }
    Require-Path $SapInstallRoot 'MISSING_SAP_INSTALL_ROOT' 'SAP install root'
    Require-Path $IdtPluginDirectory 'MISSING_IDT_PLUGIN_DIRECTORY' 'IDT plugin directory'
    Require-Path $SapJvmBinDirectory 'MISSING_SAP_JVM_DIRECTORY' 'SAP JVM bin directory'
    Require-Path $LocalIdtProjectDirectory 'MISSING_IDT_PROJECT_DIRECTORY' 'local IDT project directory'
    Require-Path $WorkingDirectory 'MISSING_WORKING_DIRECTORY' 'working directory'
    Require-Path $script:CapabilityRegistry 'MISSING_CAPABILITY_REGISTRY' 'capability registry'

    $tools = @{}
    foreach ($tool in @('java.exe', 'javac.exe', 'javap.exe', 'jar.exe')) {
        $toolPath = Join-Path $SapJvmBinDirectory $tool
        if (-not (Test-Path -LiteralPath $toolPath)) {
            throw "MISSING_JAVA_TOOL`: required SAP JVM tool is missing: $toolPath"
        }
        $tools[$tool] = $toolPath
    }

    $capabilities = Get-Content -LiteralPath $script:CapabilityRegistry -Raw | ConvertFrom-Json
    if ($capabilities.capability_status -ne 'CONFIRMED_BY_JAVAP') {
        throw 'MALFORMED_CAPABILITY_REGISTRY: capability_status must be CONFIRMED_BY_JAVAP'
    }
    if (-not $capabilities.capabilities) {
        throw 'MALFORMED_CAPABILITY_REGISTRY: capabilities array is empty'
    }

    $sdkJars = @(Invoke-Phase -Name 'JAR_INVENTORY' -Action {
        @(Get-ChildItem -LiteralPath $using:SapInstallRoot -Filter '*.jar' -File -Recurse; Get-ChildItem -LiteralPath $using:IdtPluginDirectory -Filter '*.jar' -File -Recurse) | Sort-Object FullName -Unique
    })
    if ($sdkJars.Count -eq 0) {
        throw 'MISSING_SDK_JARS: no SDK JARs found under SAP install root or IDT plugin directory'
    }

    New-Item -ItemType Directory -Force -Path $script:OutputRoot, $WorkingDirectory | Out-Null
    $jarInventory = @(Invoke-Phase -Name 'JAR_METADATA' -Action {
        $using:sdkJars | ForEach-Object {
        [ordered]@{
            file_name = $_.Name
            absolute_path = $_.FullName
            length_bytes = $_.Length
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
            copied_into_package = $false
        }
        }
    })
    $jarInventory | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $script:OutputRoot 'sdk_jar_inventory.json') -Encoding UTF8

    $classpath = ($sdkJars.FullName -join [IO.Path]::PathSeparator)
    $classpathFile = Join-Path $script:OutputRoot 'runtime_classpath.txt'
    Set-Content -LiteralPath $classpathFile -Value $classpath -Encoding UTF8

    Write-ProgressPhase 'JVM_DISCOVERY_START'
    $javaVersionResult = Invoke-InformationalNativeCommand -Executable $tools['java.exe'] -Arguments @('-version') -FailureCode 'JVM_DISCOVERY_FAILURE'
    $javaPropertiesResult = Invoke-InformationalNativeCommand -Executable $tools['java.exe'] -Arguments @('-XshowSettings:properties', '-version') -FailureCode 'JVM_DISCOVERY_FAILURE'
    $javaVersion = (($javaVersionResult.stdout -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 1) -join '').Trim()
    if (-not $javaVersion) { $javaVersion = (($javaVersionResult.stderr -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 1) -join '').Trim() }
    $javaProperties = "$($javaPropertiesResult.stdout)`n$($javaPropertiesResult.stderr)"
    Write-ProgressPhase 'JVM_DISCOVERY_COMPLETE'
    $osArchitecture = if ([Environment]::Is64BitOperatingSystem) { 'x64' } else { 'x86' }
    $jvmArchitecture = if ($javaProperties -match 'sun.arch.data.model\s*=\s*(\d+)') { "$($Matches[1])-bit" } else { 'UNKNOWN' }
    if ($osArchitecture -eq 'x64' -and $jvmArchitecture -eq '32-bit') {
        throw 'ARCHITECTURE_MISMATCH: 32-bit JVM cannot be used for the x64 BusinessObjects runtime'
    }
    $environment = [ordered]@{
        schema_version = 'route_b.sdk.v1'
        sap_install_root = (Resolve-Path $SapInstallRoot).Path
        idt_plugin_directory = (Resolve-Path $IdtPluginDirectory).Path
        sap_jvm_bin_directory = (Resolve-Path $SapJvmBinDirectory).Path
        local_idt_project_directory = (Resolve-Path $LocalIdtProjectDirectory).Path
        working_directory = (Resolve-Path $WorkingDirectory).Path
        output_directory = (Resolve-Path $OutputDirectory).Path
        java_version = $javaVersion
        jvm_architecture = $jvmArchitecture
        os_architecture = $osArchitecture
        cms_connection_attempted = $false
    }
    $environment | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $script:OutputRoot 'sdk_environment.json') -Encoding UTF8
    Write-ProgressPhase 'SDK_ENVIRONMENT_WRITTEN'

    $discoveryClassNames = @(
        'com.sap.sl.datasource.DataSource'
        'com.businessobjects.mds.datafoundation.DataFoundation'
    )
    $candidateTargets = @(Invoke-Phase -Name 'CANDIDATE_DISCOVERY' -Action {
        $targets = @(
        foreach ($jar in $sdkJars) {
            $entries = & $using:tools['jar.exe'] tf $jar.FullName 2>&1
            if ($LASTEXITCODE -ne 0) { throw "CLASSPATH_FAILURE`: jar inventory failed for $($jar.FullName)" }
            foreach ($entry in $entries) {
                if ($entry -match '\.class$') {
                    $className = (($entry -replace '/', '.') -replace '\.class$', '')
                    if ($discoveryClassNames -contains $className) {
                        [ordered]@{ jar = $jar.FullName; class = $className }
                    }
                }
            }
        }
        ) | Sort-Object jar, class -Unique
        return $targets
    })
    $candidateTargets | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $script:OutputRoot 'candidate_loading_services.json') -Encoding UTF8
    Write-ProgressPhase 'CANDIDATES_DISCOVERED'

    $javapOutput = Join-Path $script:OutputRoot 'javap_method_inventory.txt'
    Set-Content -LiteralPath $javapOutput -Value '# ROUTE_B_SDK javap inventory (deterministic per-JAR inspection)' -Encoding UTF8
    Invoke-Phase -Name 'JAVAP_DISCOVERY' -Action {
    foreach ($target in $using:candidateTargets) {
        Add-Content -LiteralPath $javapOutput -Value "`n### $($target.class) [$($target.jar)]"
        $result = & $using:tools['javap.exe'] -classpath $target.jar $target.class 2>&1
        if ($LASTEXITCODE -ne 0) {
            Add-Content -LiteralPath $javapOutput -Value "JAVAP_FAILURE: $($result -join ' ')"
        } else {
            Add-Content -LiteralPath $javapOutput -Value ($result -join "`n")
        }
    }
    } | Out-Null

    $javaSourceRoot = Join-Path $script:PackageRoot 'src\main\java'
    $compileDir = Join-Path $WorkingDirectory 'milestone-2a-classes'
    New-Item -ItemType Directory -Force -Path $compileDir | Out-Null
    $sources = @(Get-ChildItem -LiteralPath $javaSourceRoot -Filter '*.java' -File -Recurse | ForEach-Object FullName)
    $compileArguments = @('-encoding', 'UTF8', '-d', $compileDir) + $sources
    Invoke-InformationalNativeCommand -Executable $tools['javac.exe'] -Arguments $compileArguments -FailureCode 'CLASSPATH_FAILURE' | Out-Null
    $probeOutput = Join-Path $script:OutputRoot 'loading_bridge_probe.json'
    $probeClasspath = @($compileDir) + @($sdkJars | ForEach-Object { $_.DirectoryName } | Sort-Object -Unique | ForEach-Object { Join-Path $_ '*' })
    $probeClasspathArgument = $probeClasspath -join [IO.Path]::PathSeparator
    & $tools['java.exe'] -cp $probeClasspathArgument com.vistance.bo.routeb.Milestone2aProbe $script:CapabilityRegistry $probeOutput
    if ($LASTEXITCODE -ne 0) { throw 'MISSING_CONFIRMED_CLASSES: reflection probe could not load all confirmed classes' }
    $probe = Get-Content -LiteralPath $probeOutput -Raw | ConvertFrom-Json
    if ($probe.status -ne 'CONFIRMED' -or $probe.cms_connection_attempted -ne $false -or $probe.reflection_only -ne $true) {
        throw 'MALFORMED_OUTPUT: reflection probe output failed the Milestone 2A contract'
    }

    $manifest = [ordered]@{
        schema_version = 'route_b.sdk.v1'
        status = 'DISCOVERY_COMPLETE'
        cms_connection_attempted = $false
        sap_sdk_jars_copied = $false
        generated_files = @('sdk_environment.json','sdk_jar_inventory.json','validated_capabilities.json','candidate_loading_services.json','javap_method_inventory.txt','loading_bridge_findings.json','execution_report.md','hashes.sha256')
    }
    $validated = [ordered]@{
        capability_status = 'CONFIRMED_BY_JAVAP'
        validated_class_count = $capabilities.capabilities.Count
        validated_classes = @($capabilities.capabilities | ForEach-Object { $_.class } | Sort-Object -Unique)
        runtime_probe = 'reflection_only'
        cms_connection_attempted = $false
    }
    $validated | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $script:OutputRoot 'validated_capabilities.json') -Encoding UTF8
    [ordered]@{ status = 'DISCOVERY_COMPLETE'; cms_connection_attempted = $false; candidate_class_count = $candidateTargets.Count; javap_strategy = 'ONE_JAR_PER_INVOCATION'; javap_output = 'javap_method_inventory.txt'; loading_bridge = 'REQUIRED_INPUT until DataSource/DataFoundation provider/loading services are confirmed' } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $script:OutputRoot 'loading_bridge_findings.json') -Encoding UTF8
    "# Milestone 2A Execution Report`n`n- Status: DISCOVERY_COMPLETE`n- JVM: $javaVersion`n- JVM architecture: $jvmArchitecture`n- OS architecture: $osArchitecture`n- SDK JARs copied: false`n- CMS connection attempted: false`n- Candidate classes: $($candidateTargets.Count)`n- Javap strategy: one JAR per invocation; full runtime classpath never passed to javap`n- Loading bridge: REQUIRED_INPUT until DataSource/DataFoundation provider/loading services are confirmed`n" | Set-Content -LiteralPath (Join-Path $script:OutputRoot 'execution_report.md') -Encoding UTF8
    $hashLines = Get-ChildItem -LiteralPath $script:OutputRoot -File | Where-Object Name -ne 'hashes.sha256' | Sort-Object Name | ForEach-Object {
        $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
        "$hash  $($_.Name)"
    }
    Set-Content -LiteralPath (Join-Path $script:OutputRoot 'hashes.sha256') -Value $hashLines -Encoding UTF8
    $manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $script:OutputRoot 'export_manifest.json') -Encoding UTF8
    Write-Output "Milestone 2A discovery complete: $script:OutputRoot"
} catch {
    $message = $_.Exception.Message
    $code = if ($message -match '^([A-Z_]+):') { $Matches[1] } else { 'MILESTONE_2A_FAILURE' }
    Write-Failure $code $message
    throw
}
