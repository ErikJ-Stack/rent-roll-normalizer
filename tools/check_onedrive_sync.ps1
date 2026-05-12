<#
.SYNOPSIS
    Check whether OneDrive has finished syncing this repo. Run before every coding session.

.DESCRIPTION
    Verifies three things:
      1. OneDrive.exe is running.
      2. No transient sync-lock artifacts (*.tmp, ~$*, .partial, .~lock.*) exist
         anywhere in the repo.
      3. No files in the repo are marked cloud-only (offline / recall-on-open /
         recall-on-data-access). Cloud-only files will make git fail.

    If all three pass, exits 0 ("safe to work"). Otherwise exits 1 with a per-check
    report so you know exactly what to wait on.

    Scans the whole repo recursively except .venv/, __pycache__/, node_modules/,
    and other .claude/worktrees/ siblings. Includes .git/ -- cloud-only git
    objects WILL corrupt the repo, so we have to see them.

.PARAMETER Path
    Repo root to check. Defaults to the parent of this script's directory
    (i.e., the repo root when the script lives in tools/).

.PARAMETER Wait
    Poll every 5 seconds until safe, or until -TimeoutSeconds elapses.

.PARAMETER TimeoutSeconds
    For -Wait mode. Default 300 (5 minutes).

.PARAMETER VerboseLists
    Print full lists of lock files / cloud-only files. Default is first 5 only.

.EXAMPLE
    .\tools\check_onedrive_sync.ps1
    Quick one-shot check. Run at the start of every coding session.

.EXAMPLE
    .\tools\check_onedrive_sync.ps1 -Wait
    Block until OneDrive is in a clean state. Use when you just opened the
    laptop and OneDrive is still catching up.

.EXAMPLE
    .\tools\check_onedrive_sync.ps1 -Wait -TimeoutSeconds 600 -VerboseLists
    Wait up to 10 minutes, with full file lists in the report.

.NOTES
    Safe to run any time. Read-only -- never modifies any file or git state.
    Returns:
      exit 0 = safe to work
      exit 1 = OneDrive not in a clean state (lock files present or cloud-only files)
      exit 2 = path doesn't exist
#>
[CmdletBinding()]
param(
    [string]$Path,
    [switch]$Wait,
    [int]$TimeoutSeconds = 300,
    [switch]$VerboseLists
)

# Resolve repo path: if -Path was passed, use it; else use this script's parent dir.
if (-not $Path) {
    $Path = Split-Path -Parent $PSScriptRoot
}
try {
    $Path = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
} catch {
    Write-Host "ERROR: Path does not exist: $Path" -ForegroundColor Red
    exit 2
}

# File-attribute flags (Win32 constants)
$FILE_ATTRIBUTE_OFFLINE                = 0x00001000
$FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS  = 0x00400000
$FILE_ATTRIBUTE_RECALL_ON_OPEN         = 0x00040000
$CloudOnlyMask = $FILE_ATTRIBUTE_OFFLINE -bor $FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS -bor $FILE_ATTRIBUTE_RECALL_ON_OPEN

# Directories we skip: machine-local (won't sync) or other worktrees (self-checked).
# We DO include .git/ -- cloud-only git objects break everything.
$ExcludeSegments = @(
    '\.venv\',
    '\__pycache__\',
    '\node_modules\',
    '\.pytest_cache\'
)

function Should-Skip([string]$fullPath) {
    foreach ($seg in $ExcludeSegments) {
        if ($fullPath -like "*$seg*") { return $true }
    }
    return $false
}

function Get-AllFiles([string]$rootDir) {
    Get-ChildItem -LiteralPath $rootDir -Recurse -Force -File -ErrorAction SilentlyContinue |
        Where-Object { -not (Should-Skip $_.FullName) }
}

function Find-LockArtifacts($files) {
    $files | Where-Object {
        $n = $_.Name
        ($n -like '~$*') -or
        ($n -like '*.tmp') -or
        ($n -like '*.partial') -or
        ($n -like '.~lock.*')
    }
}

function Find-CloudOnlyFiles($files) {
    $files | Where-Object {
        ([int]$_.Attributes -band $CloudOnlyMask) -ne 0
    }
}

function Get-Status([string]$rootDir) {
    $proc = Get-Process OneDrive -ErrorAction SilentlyContinue
    $files = @(Get-AllFiles $rootDir)
    $artifacts = @(Find-LockArtifacts $files)
    $cloudOnly = @(Find-CloudOnlyFiles $files)
    return [pscustomobject]@{
        Path           = $rootDir
        OneDriveRunning = [bool]$proc
        TotalFiles     = $files.Count
        LockFileCount  = $artifacts.Count
        CloudOnlyCount = $cloudOnly.Count
        LockFiles      = $artifacts.FullName
        CloudOnly      = $cloudOnly.FullName
        Safe           = ([bool]$proc) -and ($artifacts.Count -eq 0) -and ($cloudOnly.Count -eq 0)
    }
}

function Show-Status($status, [bool]$compact) {
    Write-Host ""
    Write-Host "=== OneDrive Sync Check ===" -ForegroundColor Cyan
    Write-Host ("  Path:                {0}" -f $status.Path)
    Write-Host ("  Files scanned:       {0}" -f $status.TotalFiles)

    Write-Host -NoNewline "  OneDrive running:    "
    if ($status.OneDriveRunning) {
        Write-Host "yes" -ForegroundColor Green
    } else {
        Write-Host "NO -- start OneDrive first" -ForegroundColor Red
    }

    Write-Host -NoNewline "  Sync-lock artifacts: "
    if ($status.LockFileCount -eq 0) {
        Write-Host "0" -ForegroundColor Green
    } else {
        Write-Host ("{0} (sync in progress; wait)" -f $status.LockFileCount) -ForegroundColor Yellow
        $sample = if ($compact) { $status.LockFiles | Select-Object -First 5 } else { $status.LockFiles }
        $sample | ForEach-Object { Write-Host ("    {0}" -f $_) -ForegroundColor DarkGray }
        if ($compact -and $status.LockFiles.Count -gt 5) {
            Write-Host ("    ... ({0} more)" -f ($status.LockFiles.Count - 5)) -ForegroundColor DarkGray
        }
    }

    Write-Host -NoNewline "  Cloud-only files:    "
    if ($status.CloudOnlyCount -eq 0) {
        Write-Host "0" -ForegroundColor Green
    } else {
        Write-Host ("{0} -- git WILL FAIL on these" -f $status.CloudOnlyCount) -ForegroundColor Red
        $sample = if ($compact) { $status.CloudOnly | Select-Object -First 5 } else { $status.CloudOnly }
        $sample | ForEach-Object { Write-Host ("    {0}" -f $_) -ForegroundColor DarkGray }
        if ($compact -and $status.CloudOnly.Count -gt 5) {
            Write-Host ("    ... ({0} more)" -f ($status.CloudOnly.Count - 5)) -ForegroundColor DarkGray
        }
        Write-Host "    Fix: in File Explorer, right-click the repo folder ->" -ForegroundColor DarkGray
        Write-Host "         'Always keep on this device'" -ForegroundColor DarkGray
    }
    Write-Host ""
}

# ---------------------------------------------------------------------------
# Mode: quick (default) or wait
# ---------------------------------------------------------------------------
if (-not $Wait) {
    $status = Get-Status $Path
    Show-Status $status (-not $VerboseLists)
    if ($status.Safe) {
        Write-Host "OK -- safe to work." -ForegroundColor Green
        exit 0
    } else {
        Write-Host "WAIT -- OneDrive sync is not in a clean state." -ForegroundColor Yellow
        Write-Host "Hint: re-run with -Wait to poll until ready." -ForegroundColor DarkGray
        exit 1
    }
}

# Wait mode
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$lastStatus = $null
$iteration = 0
while ((Get-Date) -lt $deadline) {
    $iteration++
    $lastStatus = Get-Status $Path
    if ($lastStatus.Safe) {
        Show-Status $lastStatus (-not $VerboseLists)
        Write-Host ("OK -- safe to work (after {0} poll(s))." -f $iteration) -ForegroundColor Green
        exit 0
    }
    $msg = ("[{0:HH:mm:ss}] poll #{1}: OneDrive={2} locks={3} cloud-only={4}" -f `
            (Get-Date), $iteration, $lastStatus.OneDriveRunning, $lastStatus.LockFileCount, $lastStatus.CloudOnlyCount)
    Write-Host $msg -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

Write-Host ""
Write-Host ("TIMEOUT after {0} seconds. OneDrive still hasn't reached a clean state." -f $TimeoutSeconds) -ForegroundColor Red
if ($lastStatus) { Show-Status $lastStatus (-not $VerboseLists) }
exit 1
