<#
.SYNOPSIS
  One-step launcher for the ShipTrack dev server.

.DESCRIPTION
  - Verifies `uv` is installed.
  - Syncs dependencies (idempotent — fast if already synced).
  - If USE_POSTGRES=True in .env, checks that Postgres is reachable on
    localhost:5432 and aborts with a friendly message if it's not.
  - Applies migrations, seeds groups + admin (if env vars set), collects static.
  - Opens the browser at http://127.0.0.1:8000 once the server is ready.
  - Starts the dev server in the foreground. Ctrl+C to stop.

.NOTES
  Invoked by start.bat or run directly:
      powershell -ExecutionPolicy Bypass -File .\scripts\launch.ps1
#>
[CmdletBinding()]
param(
    [int]$Port = 8000,
    [string]$Bind = "127.0.0.1"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -Path $projectRoot

function Write-Step($msg) { Write-Host "[launch] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "[launch] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[launch] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[launch] $msg" -ForegroundColor Red }

function Pause-OnError {
    if ($Host.Name -eq "ConsoleHost") {
        Write-Host ""
        Write-Host "Press any key to close..." -ForegroundColor DarkGray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
}

# --- 1. uv check ---
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Err "uv not found on PATH."
    Write-Host "       Install it from https://docs.astral.sh/uv/getting-started/installation/"
    Pause-OnError
    exit 1
}

# --- 2. uv sync ---
Write-Step "syncing dependencies..."
uv sync --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Err "uv sync failed."
    Pause-OnError
    exit 1
}

# --- 3. Postgres reachability (only if .env says USE_POSTGRES=True) ---
$envFile = Join-Path $projectRoot ".env"
$usePostgres = $false
if (Test-Path $envFile) {
    if (Select-String -Path $envFile -Pattern '^\s*USE_POSTGRES\s*=\s*True\s*$' -Quiet) {
        $usePostgres = $true
    }
}
if ($usePostgres) {
    Write-Step "checking Postgres on localhost:5432..."
    $pgReady = $false
    try {
        $tcp = New-Object Net.Sockets.TcpClient
        $tcp.SendTimeout = 1000
        $tcp.ReceiveTimeout = 1000
        $iar = $tcp.BeginConnect("localhost", 5432, $null, $null)
        if ($iar.AsyncWaitHandle.WaitOne(2000, $false)) {
            $tcp.EndConnect($iar)
            $pgReady = $tcp.Connected
        }
        $tcp.Close()
    } catch { }
    if (-not $pgReady) {
        Write-Err "Postgres is not reachable on localhost:5432."
        Write-Host "       Either start the 'postgresql-x64-17' Windows service, or"
        Write-Host "       edit .env and set USE_POSTGRES=False to use SQLite locally."
        Pause-OnError
        exit 1
    }
}

# --- 4. Migrate ---
Write-Step "applying migrations..."
uv run python manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) { Write-Err "migrate failed."; Pause-OnError; exit 1 }

# --- 5. Seed groups + (optional) admin ---
Write-Step "seeding groups + admin..."
uv run python manage.py seed_demo

# --- 6. Open browser when ready (background job) ---
$url = "http://${Bind}:${Port}"
Start-Job -Name "shiptrack-open-browser" -ScriptBlock {
    param($u)
    $deadline = (Get-Date).AddSeconds(30)
    do {
        Start-Sleep -Milliseconds 400
        try {
            $r = Invoke-WebRequest -Uri "$u/healthz/" -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
            if ($r.StatusCode -eq 200) { Start-Process $u; return }
        } catch { }
    } while ((Get-Date) -lt $deadline)
} -ArgumentList $url | Out-Null

# --- 7. Start the dev server (foreground) ---
Write-Host ""
Write-Ok "starting ShipTrack at $url"
Write-Ok "press Ctrl+C to stop"
Write-Host ""
uv run python manage.py runserver "${Bind}:${Port}"
