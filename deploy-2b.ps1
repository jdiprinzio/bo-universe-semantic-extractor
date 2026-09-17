$ErrorActionPreference = "Stop"

$pkg = ".\remote-sdk-extractor\dist\milestone-2b-provider-discovery"
$zip = ".\milestone-2b-package.zip"

# ─── NEW BLOCK STARTS HERE ───────────────────────────────
Write-Host "=== Handoff simulation ===" -ForegroundColor Cyan

python -m pytest tests/ -k "handoff or simulation" -q
if ($LASTEXITCODE -ne 0) {
    throw "Handoff validation failed. Do not deploy."
}

Write-Host "OK: handoff simulation passed"
Write-Host ""
# ─── NEW BLOCK ENDS HERE ─────────────────────────────────

Write-Host "=== Verifying package ===" -ForegroundColor Cyan

if (-not (Test-Path $pkg)) { throw "Package folder not found: $pkg" }

$checks = @(
    @{ Name = "Parent-dir traversal"; Pattern = "\.\.\\"; Files = "$pkg\*.ps1"; ExpectMatch = $false }
    @{ Name = "Developer paths";      Pattern = "GITHub|jdiprinzio"; Files = "$pkg\*"; ExpectMatch = $false }
    @{ Name = "Stop-Job -Force";      Pattern = "Stop-Job.*-Force"; Files = "$pkg\*.ps1"; ExpectMatch = $false }
)

$failed = $false
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

# ─── UPDATE THIS MARKER LIST FOR THE CONSOLIDATED RELEASE ───
foreach ($marker in @(
    "PROBE_SCOPE",
    "isAssignableFrom",
    "related_return_type_inventory",
    "URLClassLoader",
    "walkFileTree",
    "Xmx4g"
)) {
    $found = Select-String -Path "$pkg\*","$pkg\src\main\java\com\vistance\bo\routeb\*" -Pattern $marker -ErrorAction SilentlyContinue
    if ($found) { Write-Host "OK: $marker present" }
    else { Write-Warning "MISSING: $marker not found"; $failed = $true }
}

if ($failed) { throw "Package verification failed. Do not deploy." }

Write-Host ""
Write-Host "=== Packaging ===" -ForegroundColor Cyan

Remove-Item $zip -Force -ErrorAction SilentlyContinue
Compress-Archive -Path "$pkg\*" -DestinationPath $zip -Force

Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path $zip))
$rootEntry = $archive.Entries | Where-Object { $_.FullName -eq "run-provider-discovery.ps1" }
$entryCount = $archive.Entries.Count
$archive.Dispose()

if (-not $rootEntry) { throw "run-provider-discovery.ps1 not at ZIP root." }

Write-Host "OK: ZIP created with $entryCount entries"
Write-Host ""
Write-Host "Ready to copy to remote machine:" -ForegroundColor Green
Write-Host (Resolve-Path $zip)