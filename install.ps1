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
$installRoot = Join-Path $env:LOCALAPPDATA 'Programs'
$target = Join-Path $installRoot 'HandMouse'
$next = Join-Path $installRoot 'HandMouse.new'
$backup = "$target.old"

New-Item -ItemType Directory -Path $work -Force | Out-Null
try {
    Invoke-WebRequest "$assetBase/HandMouse-Windows.zip" -OutFile $archive
    Invoke-WebRequest "$assetBase/HandMouse-Windows.zip.sha256" -OutFile $digest
    $expected = (Get-Content -Raw $digest).Trim().Split(' ')[0].ToUpperInvariant()
    if ($expected -notmatch '^[0-9A-F]{64}$') { throw 'Invalid release checksum.' }
    $actual = (Get-FileHash $archive -Algorithm SHA256).Hash
    if ($actual -ne $expected) { throw 'Release checksum mismatch. Nothing was installed.' }

    Expand-Archive -LiteralPath $archive -DestinationPath $stage -Force
    $source = Join-Path $stage 'HandMouse'
    $sourceExe = Join-Path $source 'HandMouse.exe'
    if (-not (Test-Path -LiteralPath $sourceExe -PathType Leaf)) {
        $matches = @(Get-ChildItem -LiteralPath $stage -Filter 'HandMouse.exe' -File -Recurse)
        if ($matches.Count -ne 1) { throw 'Release archive does not contain exactly one HandMouse.exe.' }
        $source = $matches[0].Directory.FullName
        $sourceExe = $matches[0].FullName
    }
    if ((Get-Item -LiteralPath $sourceExe).Length -le 0) { throw 'HandMouse.exe in the release is empty.' }

    New-Item -ItemType Directory -Path $installRoot -Force | Out-Null
    if (Test-Path -LiteralPath $next) { Remove-Item -LiteralPath $next -Recurse -Force }
    New-Item -ItemType Directory -Path $next -Force | Out-Null
    Get-ChildItem -LiteralPath $source -Force | Copy-Item -Destination $next -Recurse -Force

    $nextExe = Join-Path $next 'HandMouse.exe'
    if (-not (Test-Path -LiteralPath $nextExe -PathType Leaf)) { throw 'The downloaded app could not be copied into the install folder.' }
    if ((Get-Item -LiteralPath $nextExe).Length -le 0) { throw 'The copied HandMouse.exe is empty.' }

    if (Test-Path $backup) { Remove-Item -LiteralPath $backup -Recurse -Force }
    if (Test-Path $target) { Move-Item -LiteralPath $target -Destination $backup }
    try {
        Move-Item -LiteralPath $next -Destination $target
        $installedExe = Join-Path $target 'HandMouse.exe'
        if (-not (Test-Path -LiteralPath $installedExe -PathType Leaf)) { throw 'HandMouse.exe is missing after installation.' }
        if ((Get-Item -LiteralPath $installedExe).Length -le 0) { throw 'Installed HandMouse.exe is empty.' }
    } catch {
        if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force }
        if (Test-Path $backup) { Move-Item -LiteralPath $backup -Destination $target }
        throw
    }
    if (Test-Path $backup) { Remove-Item -LiteralPath $backup -Recurse -Force }

    $shell = New-Object -ComObject WScript.Shell
    $desktop = $shell.SpecialFolders.Item('Desktop')
    if ([string]::IsNullOrWhiteSpace($desktop)) { throw 'Windows Desktop folder could not be found.' }
    $shortcutPath = Join-Path $desktop 'HandMouse.lnk'
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $installedExe
    $shortcut.WorkingDirectory = $target
    $shortcut.IconLocation = "$installedExe,0"
    $shortcut.Description = 'Hand-tracking mouse'
    $shortcut.Save()
    if (-not (Test-Path -LiteralPath $shortcutPath -PathType Leaf)) { throw 'Desktop shortcut could not be created.' }

    Write-Host "Installed HandMouse to $target"
    Write-Host "Created desktop shortcut at $shortcutPath"
    Start-Process -FilePath $installedExe -WorkingDirectory $target
} finally {
    if (Test-Path -LiteralPath $next) { Remove-Item -LiteralPath $next -Recurse -Force -ErrorAction SilentlyContinue }
    Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
}

