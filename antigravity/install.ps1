<#
Install the antigravity skill for Claude Code on Windows.

    .\install.ps1                    for you, in every project
    .\install.ps1 -Project <dir>     for one repository only

Respects CLAUDE_CONFIG_DIR. An existing copy is moved aside, never deleted.
#>
param([string]$Project)

$ErrorActionPreference = 'Stop'
$src   = $PSScriptRoot
$files = 'SKILL.md', 'agy_watch.py', 'README.md', 'LICENSE'

if ($Project) {
    if (-not (Test-Path -LiteralPath $Project -PathType Container)) { throw "no such directory: $Project" }
    $dest = Join-Path (Resolve-Path -LiteralPath $Project).Path '.claude\skills\antigravity'
} else {
    $root = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $HOME '.claude' }
    $dest = Join-Path $root 'skills\antigravity'
}

foreach ($f in $files) {
    if (-not (Test-Path -LiteralPath (Join-Path $src $f))) { throw "missing $f next to install.ps1 - extract the whole zip first" }
}

$same = (Test-Path -LiteralPath $dest) -and ((Resolve-Path -LiteralPath $dest).Path -eq (Resolve-Path -LiteralPath $src).Path)
if ($same) {
    "already in place: $dest"
} else {
    if (Test-Path -LiteralPath $dest) {
        # outside skills\: a copy left there would load as a second skill with the same name
        $backups = Join-Path (Split-Path (Split-Path $dest)) 'skill-backups'
        New-Item -ItemType Directory -Force -Path $backups | Out-Null
        $old = Join-Path $backups "antigravity-$(Get-Date -Format yyyyMMdd-HHmmss)"
        Move-Item -LiteralPath $dest -Destination $old
        "previous copy moved to: $old"
    }
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    foreach ($f in $files) { Copy-Item -LiteralPath (Join-Path $src $f) -Destination (Join-Path $dest $f) }
    "installed: $dest"
}

# The watcher needs Python 3.8+. A bare `python` on Windows may be the Store stub, so check the version.
$py = $null
foreach ($c in @(@('python3'), @('python'), @('py', '-3'))) {
    if (-not (Get-Command $c[0] -ErrorAction SilentlyContinue)) { continue }
    $args_ = @($c | Select-Object -Skip 1) + @('-c', 'import sys; sys.exit(sys.version_info < (3, 8))')
    & $c[0] @args_ 2>$null
    if ($LASTEXITCODE -eq 0) { $py = $c; break }
}
if ($py) {
    $args_ = @($py | Select-Object -Skip 1) + @('-I', (Join-Path $dest 'agy_watch.py'), '--help')
    & $py[0] @args_ > $null
    if ($LASTEXITCODE -eq 0) { "watcher ok ($($py -join ' '))" }
} else {
    Write-Warning 'no Python 3.8+ found; the skill needs it to watch dispatches'
}

@'

Next:
  1. Run `agy` once and finish the browser sign-in (skip if Antigravity is already signed in).
  2. In Claude Code, type:  /antigravity setup
'@
