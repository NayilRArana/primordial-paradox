<#
  run.ps1: the one command. It checks the data, regenerates the project files, then builds and launches the game with
  Igor. Nothing it starts opens a console window of its own; the only window you see is the game.

  Usage, from anywhere:
      powershell -NoProfile -ExecutionPolicy Bypass -File "<repo>\tools\run.ps1"
  or double click tools\run.vbs, which runs this script with no console at all.

  Exit codes:
      0  the build finished: the game launched, or with -Compile it compiled and nothing was launched
      1  a data or project check failed (the game was NOT built)
      2  GameMaker is not installed, or Igor is there but no licence folder exists yet
      3  Igor ran and returned an error (the last 20 lines are printed)

  Status: VERIFIED 2026-10-20. GameMaker LTS2026 is installed on this PC: runtime-2026.0.0.23, Igor shipping inside the
  runtime at bin\igor\windows\x64\Igor.exe, and the account folder at %APPDATA%\GameMakerStudio2-LTS2026. Those folder
  names are not the 2024 ones this script was first written against, so the discovery below matches both lines.
  -Compile builds and stops; -SkipChecks skips the Python gates.
  Igor's Run WAITS for the launched game to exit (measured 2026-10-25), so anything that wants only a build, and that is
  the push gate's step, passes -Compile. Run stays what a human double clicks when he wants to play.

  The talk bridge (card W1 PP-BRIDGE, added 2026-10-26). With no -Compile and no -NoBridge this script starts
  tools\ai_bridge.py before Igor and stops it after the game closes, so the talk fight gets a live verdict from the
  local model and a transcript from faster-whisper. It listens on 127.0.0.1 only, its log is build\last-bridge.log, and
  a bridge that will not start is a printed warning rather than a failed build: the game still runs, and the talk fight
  falls back to the recorded answers in data\ai_cache\bridge. -NoBridge is for anything that must not start a server.
#>

[CmdletBinding()]
param(
    [switch]$SkipChecks,
    [switch]$Compile,
    [switch]$NoBridge
)

$ErrorActionPreference = 'Stop'
$root  = Split-Path -Parent $PSScriptRoot
$game  = Join-Path $root 'game'
$yyp   = Join-Path $game 'PrimordialParadox.yyp'
$build = Join-Path $root 'build'
$log   = Join-Path $build 'last-build.log'
$igorLog = Join-Path $build 'last-igor.log'

New-Item -ItemType Directory -Force -Path $build | Out-Null
if (Test-Path $log) { Remove-Item $log -Force }
if (Test-Path $igorLog) { Remove-Item $igorLog -Force }

function Say([string]$message) {
    Write-Host $message
    Add-Content -Path $log -Value $message
}

function Fail([int]$code, [string]$message) {
    Say $message
    exit $code
}

# ---------------------------------------------------------------------------------------------------------------
# 1. Data and project checks. These are the gates that do not need GameMaker, so a broken data file stops here with a
#    readable message instead of a mystery at runtime.

$python = $null
foreach ($candidate in @('python', 'py')) {
    $found = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($null -ne $found) { $python = $found.Source; break }
}
if ($null -eq $python) { Fail 1 'Python is not on PATH, so the data checks cannot run. Install Python or run the checks by hand.' }

if (-not $SkipChecks) {
    foreach ($script in @('sync_data.py', 'sync_art.py', 'check_data.py', 'gen_project.py', 'check_project.py', 'check_cleanroom.py', 'check_provenance.py')) {
        $path = Join-Path $root "tools\$script"
        Say "running $script"
        $output = & $python $path 2>&1
        $code = $LASTEXITCODE
        foreach ($line in $output) { Add-Content -Path $log -Value $line }
        if ($code -ne 0) {
            foreach ($line in $output) { Write-Host $line }
            Fail 1 "$script failed (exit $code). The game was not built. Full log: $log"
        }
    }
}

# ---------------------------------------------------------------------------------------------------------------
# 2. Find the runtime, Igor and the licence folder.

$runtime = $env:PP_RUNTIME
if ([string]::IsNullOrWhiteSpace($runtime)) {
    # Two folder names exist in the wild: "GameMakerStudio2" for the 2024 line and "GameMakerStudio2-LTS2026" for the LTS
    # line installed here. Match either, and take the newest runtime by name.
    $runtimes = @()
    foreach ($wildcard in @('GameMakerStudio2', 'GameMakerStudio2-*')) {
        $productRoots = Get-ChildItem -Path $env:ProgramData -Directory -Filter $wildcard -ErrorAction SilentlyContinue
        foreach ($product in $productRoots) {
            $runtimeRoot = Join-Path $product.FullName 'Cache\runtimes'
            if (Test-Path $runtimeRoot) {
                $runtimes += Get-ChildItem -Path $runtimeRoot -Directory -Filter 'runtime-*' -ErrorAction SilentlyContinue
            }
        }
    }
    if ($runtimes.Count -gt 0) {
        $runtime = $runtimes | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty FullName
    }
}
if ([string]::IsNullOrWhiteSpace($runtime)) {
    Fail 2 'GameMaker Studio is not installed on this PC (no runtime folder), so there is nothing to build yet. Install it and log in once, then run this again.'
}
if (-not (Test-Path $runtime)) { Fail 2 "PP_RUNTIME points at $runtime, which does not exist." }

$igor = $null
foreach ($relative in @('bin\igor\windows\x64\Igor.exe', 'bin\igor\windows\x86\Igor.exe', 'bin\igor\windows\Igor.exe')) {
    $candidate = Join-Path $runtime $relative
    if (Test-Path $candidate) { $igor = $candidate; break }
}
if ($null -eq $igor) { Fail 2 "The runtime at $runtime has no Igor.exe, so the command line build cannot run. Open GameMaker once and let it finish installing the runtime." }

$userFolder = $null
foreach ($wildcard in @('GameMakerStudio2', 'GameMakerStudio2-*')) {
    if ($null -ne $userFolder) { break }
    $productRoots = Get-ChildItem -Path $env:APPDATA -Directory -Filter $wildcard -ErrorAction SilentlyContinue
    foreach ($product in $productRoots) {
        # A named account lives in a subfolder ending in _<digits>. That is the folder the 2024 line wants.
        $account = Get-ChildItem -Path $product.FullName -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match '_\d+$' } |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if ($null -ne $account) { $userFolder = $account.FullName; break }
        # The LTS line keeps um.json in the product folder itself and takes that folder as the user folder. Only trust
        # this for the '-suffix' product folder, never for the 2024 one, where a missing account must still stop the build.
        if ($product.Name -ne 'GameMakerStudio2' -and (Test-Path (Join-Path $product.FullName 'um.json'))) {
            $userFolder = $product.FullName
            break
        }
    }
}
if ([string]::IsNullOrWhiteSpace($userFolder)) {
    Fail 2 'Igor needs a licence folder and there is none yet. Open GameMaker Studio once, log in, then run this again. (That login is your step, not the bot''s.)'
}

if (-not (Test-Path $yyp)) { Fail 1 "The project file is missing: $yyp" }

# ---------------------------------------------------------------------------------------------------------------
# 3. The talk bridge, when the game is going to be played rather than only compiled.
#
# Started here, after the runtime and licence are known good, so a Fail above never leaves a server running. -Compile
# skips it: the push gate compiles on a machine that may have no model loaded, and a compile must not depend on one.
# A bridge that will not answer is a warning, not a failed build: the game still plays, every talk turn falls to the
# recorded answer, and the reason is in build\last-bridge.log.

$bridgePid = $null
if (-not $Compile -and -not $NoBridge) {
    $bridgeScript = Join-Path $root 'tools\ai_bridge.py'
    $bridgeLog = Join-Path $build 'last-bridge.log'
    $bridgeErr = Join-Path $build 'last-bridge-error.log'
    foreach ($stale in @($bridgeLog, $bridgeErr)) { if (Test-Path $stale) { Remove-Item $stale -Force } }
    $bridgePort = 8791
    if (-not [string]::IsNullOrWhiteSpace($env:PP_BRIDGE_PORT)) {
        $parsed = 0
        if ([int]::TryParse($env:PP_BRIDGE_PORT, [ref]$parsed) -and $parsed -gt 0) { $bridgePort = $parsed }
    }
    try {
        $bridge = Start-Process -FilePath $python `
            -ArgumentList @("`"$bridgeScript`"", '--serve', '--warm', '--port', "$bridgePort") `
            -WorkingDirectory $root -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput $bridgeLog -RedirectStandardError $bridgeErr
        $bridgePid = $bridge.Id
        # The parent exits through Fail() on some paths, which does not run a finally block, so the stop is also
        # registered on the engine's own exit event. The pid travels in the event's MessageData because an action
        # script block runs in its own runspace and cannot see this script's variables.
        $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -MessageData $bridgePid -Action {
            if ($event.MessageData) {
                Stop-Process -Id $event.MessageData -Force -ErrorAction SilentlyContinue
            }
        }
        $ready = $false
        $deadline = (Get-Date).AddSeconds(20)
        while ((Get-Date) -lt $deadline) {
            $client = New-Object System.Net.Sockets.TcpClient
            try {
                $connect = $client.ConnectAsync('127.0.0.1', $bridgePort)
                if ($connect.Wait(400) -and $client.Connected) { $ready = $true; break }
            } catch {
            } finally {
                $client.Close()
            }
            if ($bridge.HasExited) { break }
            Start-Sleep -Milliseconds 250
        }
        if ($ready) {
            Say "talk bridge: http://127.0.0.1:$bridgePort (log: $bridgeLog)"
        } else {
            $reason = Get-Content -Path $bridgeErr -Tail 3 -ErrorAction SilentlyContinue
            foreach ($line in $reason) { Say "talk bridge stderr: $line" }
            Say "talk bridge did not answer on 127.0.0.1:$bridgePort. The game still runs; talk falls back to the recorded answers."
        }
    } catch {
        Say "talk bridge could not be started ($($_.Exception.Message)). The game still runs; talk falls back to the recorded answers."
    }
}

# ---------------------------------------------------------------------------------------------------------------
# 4. Build and run.

$mode = 'Run'
if ($Compile) { $mode = 'Compile' }

# The flag forms below are the ones measured working against runtime-2026.0.0.23 on 2026-10-20. /cache and /temp are
# deliberately not passed: they were never proven on this runtime, and an unproven flag here would fail the build in a way
# that reads as the project being broken.
$arguments = @(
    "--project=`"$yyp`"",
    "--runtimePath=`"$runtime`"",
    "--uf=`"$userFolder`"",
    '--config=Default',
    '--', 'Windows', $mode
)

Say "building with $igor"
Say "game: $yyp"
Say "gate log:  $log"
Say "build log: $igorLog"

# Igor writes to its own file. Redirecting it onto the gate log would truncate the check output a user needs most when
# a build fails, and Start-Process truncates a redirect target.
#
# -WorkingDirectory is not optional. Igor resolves its cache and temp folders against the CURRENT directory, not
# against the project, so run from anywhere else it tries to create them under that folder and stops with
# "UnauthorizedAccessException: Access to the path '<current folder>\cache\PrimordialParadox' is denied" (measured
# 2026-10-20). The project root is the folder that holds the cache and output folders the build writes into.
$process = Start-Process -FilePath $igor -ArgumentList $arguments -WorkingDirectory $root -NoNewWindow -PassThru -Wait `
    -RedirectStandardOutput $igorLog -RedirectStandardError (Join-Path $build 'last-build-error.log')

if ($process.ExitCode -ne 0) {
    $tail = Get-Content -Path $igorLog -Tail 20 -ErrorAction SilentlyContinue
    foreach ($line in $tail) { Write-Host $line }
    if ($null -ne $bridgePid) { Stop-Process -Id $bridgePid -Force -ErrorAction SilentlyContinue }
    Fail 3 "Igor returned $($process.ExitCode). The last 20 lines are above. Build log: $igorLog. Gate log: $log"
}

# The game has closed (Igor's Run waits for it), so the bridge has nothing left to answer. Stopping it here is also
# what keeps a second run from finding the port taken.
if ($null -ne $bridgePid) {
    Stop-Process -Id $bridgePid -Force -ErrorAction SilentlyContinue
    Say 'talk bridge stopped.'
}

if ($Compile) {
    Say 'Igor finished: the project compiled, and nothing was launched (that is what -Compile means).'
} else {
    Say 'Igor finished. The game window is the only window that opened.'
}
exit 0
