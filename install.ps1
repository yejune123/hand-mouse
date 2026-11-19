param(
    [string]$Repository = 'yejune123/hand-mouse'
)

$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'This installer requires Windows.' }

$assetBase = "https://github.com/$Repository/releases/latest/download"
$work = Join-Path ([IO.Path]::GetTempPath()) ("HandMouse-" + [guid]::NewGuid().ToString('N'))
$archive = Join-Path $work 'HandMouse-Windows.zip'
$digest = Join-Path $work 'HandMouse-Windows.zip.sha256'
$stage = Join-Path $work 'unpacked'
$target = Join-Path $env:LOCALAPPDATA 'Programs\HandMouse'
$backup = "$target.old"

New-Item -ItemType Directory -Path $work -Force | Out-Null
try {
    Invoke-WebRequest "$assetBase/HandMouse-Windows.zip" -OutFile $archive
    Invoke-WebRequest "$assetBase/HandMouse-Windows.zip.sha256" -OutFile $digest
    $expected = (Get-Content -Raw $digest).Trim().Split(' ')[0].ToUpperInvariant()
    if ($expected -notmatch '^[0-9A-F]{64}$') { throw 'Invalid release checksum.' }
    $actual = (Get-FileHash $archive -Algorithm SHA256).Hash
    if ($actual -ne $expected) { throw 'Release checksum mismatch. Nothing was installed.' }

    Expand-Archive -LiteralPath $archive -DestinationPath $stage
    $source = Join-Path $stage 'HandMouse'
    if (-not (Test-Path (Join-Path $source 'HandMouse.exe'))) { throw 'Release archive does not contain HandMouse.exe.' }
    New-Item -ItemType Directory -Path (Split-Path $target) -Force | Out-Null
    if (Test-Path $backup) { Remove-Item -LiteralPath $backup -Recurse -Force }
    if (Test-Path $target) { Move-Item -LiteralPath $target -Destination $backup }
    try {
        Move-Item -LiteralPath $source -Destination $target
    } catch {
        if (Test-Path $backup) { Move-Item -LiteralPath $backup -Destination $target }
        throw
    }
    if (Test-Path $backup) { Remove-Item -LiteralPath $backup -Recurse -Force }
    Write-Host "Installed HandMouse to $target"
    Start-Process -FilePath (Join-Path $target 'HandMouse.exe')
} finally {
    Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
}
