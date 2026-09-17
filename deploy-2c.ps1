$ErrorActionPreference = "Stop"

$pkg = ".\remote-sdk-extractor\dist\milestone-2c-universe-loader-discovery"
$zip = ".\milestone-2c-package.zip"

Write-Host "=== Java import validation ===" -ForegroundColor Cyan

python -m pytest tests/ -k "import_validator" -q
if ($LASTEXITCODE -ne 0) { throw "Java import validation failed. Do not deploy." }

Write-Host "OK: import validation passed"

Write-Host ""
Write-Host "=== Verifying package ===" -ForegroundColor Cyan

if (-not (Test-Path $pkg)) { throw "Package folder not found: $pkg" }

$failed = $false

$checks = @(
    @{ Name = "Parent-dir traversal"; Pattern = "\.\.\\"; Files = "$pkg\*.ps1" }
    @{ Name = "Developer paths";      Pattern = "GITHub|jdiprinzio"; Files = "$pkg\*" }
    @{ Name = "Start-Job usage";      Pattern = "Start-Job"; Files = "$pkg\*.ps1" }
)

foreach ($c in $checks) {
    $hits = Select-String -Path $c.Files -Pattern $c.Pattern -ErrorAction SilentlyContinue
    if ($hits) {
        Write-Warning "FAIL: $($c.Name)"
        $hits | Select-Object Filename,LineNumber,Line | Format-Table -AutoSize
        $failed = $true
    } else {
        Write-Host "OK: $($c.Name) clean"
    }
}

$binaries = Get-ChildItem $pkg -Recurse -Include *.jar,*.class -ErrorAction SilentlyContinue
if ($binaries) {
    Write-Warning "FAIL: SAP binaries present in package"
    $binaries | Select-Object FullName | Format-Table -AutoSize
    $failed = $true
} else {
    Write-Host "OK: no JAR or class files"
}

Write-Host ""
Write-Host "=== Expected markers ===" -ForegroundColor Cyan

foreach ($marker in @(
    "UniverseLoaderProbe",
    "isAssignableFrom",
    "URLClassLoader",
    "FILE_BASED",
    "CMS_BASED",
    "DataFoundationFile",
    "TARGET_CLASSES_UNLOADABLE",
    "Xmx4g"
)) {
    $found = Select-String -Path "$pkg\*","$pkg\src\main\java\com\vistance\bo\routeb\*" -Pattern $marker -ErrorAction SilentlyContinue
    if ($found) { Write-Host "OK: $marker present" }
    else { Write-Warning "MISSING: $marker"; $failed = $true }
}

if ($failed) { throw "Package verification failed. Do not deploy." }

Write-Host ""
Write-Host "=== Packaging ===" -ForegroundColor Cyan

Remove-Item $zip -Force -ErrorAction SilentlyContinue
Compress-Archive -Path "$pkg\*" -DestinationPath $zip -Force

Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path $zip))
$root = $archive.Entries | Where-Object { $_.FullName -eq "run-universe-loader-discovery.ps1" }
$count = $archive.Entries.Count
$archive.Dispose()

if (-not $root) { throw "run-universe-loader-discovery.ps1 not at ZIP root." }

Write-Host "OK: ZIP created with $count entries"
Write-Host ""
Write-Host "Ready to copy:" -ForegroundColor Green
Write-Host (Resolve-Path $zip)