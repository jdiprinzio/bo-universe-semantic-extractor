[CmdletBinding()]
param([string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path)

$ErrorActionPreference = 'Stop'
. (Join-Path $RepoRoot 'remote-sdk-extractor\scripts\invoke-informational-native.ps1')
$temp = Join-Path ([IO.Path]::GetTempPath()) ("route-b-javac-test-" + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $temp | Out-Null
try {
    foreach ($case in @(
        @{ Name = 'note'; Text = 'Note: source uses unchecked operations'; Code = 0 },
        @{ Name = 'warning'; Text = 'warning: unchecked conversion'; Code = 0 },
        @{ Name = 'stderr'; Text = 'compiler informational stderr'; Code = 0 }
    )) {
        $command = Join-Path $temp ($case.Name + '.cmd')
        "@echo $($case.Text) 1>&2`r`n@exit /b $($case.Code)" | Set-Content -LiteralPath $command -Encoding ASCII
        $output = Invoke-InformationalNativeCommand -Executable $command -Arguments @('-encoding', 'UTF8') -FailureCode 'CLASSPATH_FAILURE'
        if ($output -notmatch [regex]::Escape($case.Text)) { throw "$($case.Name) stderr was not captured" }
    }

    $failure = Join-Path $temp 'failure.ps1'
    'Write-Error "javac fatal error"; exit 2' | Set-Content -LiteralPath $failure -Encoding UTF8
    try {
        Invoke-InformationalNativeCommand -Executable (Get-Command powershell.exe).Source -Arguments @('-NoProfile', '-File', $failure) -FailureCode 'CLASSPATH_FAILURE' | Out-Null
        throw 'non-zero javac exit did not fail'
    } catch {
        if ($_.Exception.Message -notmatch 'CLASSPATH_FAILURE') { throw }
    }

    Write-Output 'Milestone 2A javac output tests passed'
} finally {
    Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
}
