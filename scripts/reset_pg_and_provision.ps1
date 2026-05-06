<#
.SYNOPSIS
  Reset the local Postgres `postgres` superuser password AND provision the
  project database + user in a single elevated run.

.DESCRIPTION
  Steps (all wrapped in try/finally so pg_hba.conf is always restored):
    1. Verify the script is running as Administrator.
    2. Stop the postgresql-x64-17 service.
    3. Back up pg_hba.conf with a timestamp.
    4. Write a temporary pg_hba.conf that allows trust-mode auth from localhost.
    5. Start the service.
    6. Connect as postgres (no password), set the new password, then create
       the project database and user, granting all privileges.
    7. Stop the service.
    8. Restore the original pg_hba.conf.
    9. Start the service.
   10. Verify the new password works.

  Passwords are prompted interactively (Read-Host -AsSecureString) so they are
  never written to shell history or to disk. Passwords ARE briefly converted to
  plaintext in process memory to pass to psql via PGPASSWORD — that is
  unavoidable for psql auth and the script clears the variable when done.

.NOTES
  Run from an elevated PowerShell prompt:
      powershell -ExecutionPolicy Bypass -File .\scripts\reset_pg_and_provision.ps1
#>
[CmdletBinding()]
param(
    [string]$ProjectDb = "shiptrack",
    [string]$ProjectUser = "shiptrack",
    [string]$DataDir = "C:\Program Files\PostgreSQL\17\data",
    [string]$BinDir = "C:\Program Files\PostgreSQL\17\bin",
    [string]$ServiceName = "postgresql-x64-17"
)

$ErrorActionPreference = "Stop"

function Assert-Admin {
    $id = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $p = New-Object System.Security.Principal.WindowsPrincipal($id)
    if (-not $p.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "This script must be run from an elevated (Run as Administrator) PowerShell."
    }
}

function ConvertTo-PlainText {
    param([System.Security.SecureString]$Secure)
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secure)
    try {
        return [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
    } finally {
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

function Wait-PgReady {
    param([string]$BinDir, [int]$TimeoutSeconds = 30)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        & "$BinDir\pg_isready.exe" -h localhost -p 5432 -q
        if ($LASTEXITCODE -eq 0) { return }
        Start-Sleep -Milliseconds 500
    }
    throw "Postgres did not become ready within $TimeoutSeconds seconds."
}

function Invoke-Psql {
    param(
        [string]$BinDir,
        [string]$DbUser = "postgres",
        [string]$DbName = "postgres",
        [string]$Password = $null,
        [Parameter(Mandatory = $true)][string]$Sql
    )
    if ($Password) { $env:PGPASSWORD = $Password } else { Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue }
    try {
        $output = & "$BinDir\psql.exe" -h localhost -U $DbUser -d $DbName -v ON_ERROR_STOP=1 -tAc $Sql 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "psql failed: $output"
        }
        if ($null -eq $output) { return "" }
        return ($output | Out-String).Trim()
    } finally {
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    }
}

# --- main ---
Assert-Admin

if (-not (Test-Path "$DataDir\pg_hba.conf")) {
    throw "pg_hba.conf not found at $DataDir\pg_hba.conf - check -DataDir."
}
if (-not (Test-Path "$BinDir\psql.exe")) {
    throw "psql.exe not found at $BinDir - check -BinDir."
}

Write-Host "Database to create: $ProjectDb"
Write-Host "User to create:     $ProjectUser"
Write-Host ""

$pgSecure = Read-Host -AsSecureString "Enter NEW password for the 'postgres' superuser"
$pgConfirm = Read-Host -AsSecureString "Confirm 'postgres' password"
if ((ConvertTo-PlainText $pgSecure) -ne (ConvertTo-PlainText $pgConfirm)) {
    throw "postgres passwords do not match."
}

$projSecure = Read-Host -AsSecureString "Enter password for the project user '$ProjectUser'"
$projConfirm = Read-Host -AsSecureString "Confirm '$ProjectUser' password"
if ((ConvertTo-PlainText $projSecure) -ne (ConvertTo-PlainText $projConfirm)) {
    throw "project passwords do not match."
}

$pgPlain = ConvertTo-PlainText $pgSecure
$projPlain = ConvertTo-PlainText $projSecure

$hbaPath = Join-Path $DataDir "pg_hba.conf"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = "$hbaPath.bak.$timestamp"

$trustHba = @"
# TEMPORARY pg_hba.conf written by reset_pg_and_provision.ps1
# The original file was backed up to $backupPath and will be restored
# automatically when this script finishes (or fails).
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
local   replication     all                                     trust
host    replication     all             127.0.0.1/32            trust
host    replication     all             ::1/128                 trust
"@

$restored = $false
try {
    Write-Host "[1/9] Backing up pg_hba.conf -> $backupPath" -ForegroundColor Cyan
    Copy-Item -Path $hbaPath -Destination $backupPath -Force

    Write-Host "[2/9] Stopping service $ServiceName" -ForegroundColor Cyan
    Stop-Service -Name $ServiceName -Force
    (Get-Service -Name $ServiceName).WaitForStatus("Stopped", "00:00:30")

    Write-Host "[3/9] Writing trust-mode pg_hba.conf" -ForegroundColor Cyan
    Set-Content -Path $hbaPath -Value $trustHba -Encoding ASCII

    Write-Host "[4/9] Starting service in trust mode" -ForegroundColor Cyan
    Start-Service -Name $ServiceName
    Wait-PgReady -BinDir $BinDir

    Write-Host "[5/9] Resetting postgres password" -ForegroundColor Cyan
    $escapedPg = $pgPlain -replace "'", "''"
    Invoke-Psql -BinDir $BinDir -Sql "ALTER USER postgres WITH PASSWORD '$escapedPg';" | Out-Null

    Write-Host "[6/9] Provisioning project DB and user" -ForegroundColor Cyan
    $escapedProj = $projPlain -replace "'", "''"
    $userExists = Invoke-Psql -BinDir $BinDir -Sql "SELECT 1 FROM pg_roles WHERE rolname='$ProjectUser';"
    if ($userExists -eq "1") {
        Invoke-Psql -BinDir $BinDir -Sql "ALTER USER $ProjectUser WITH PASSWORD '$escapedProj';" | Out-Null
    } else {
        Invoke-Psql -BinDir $BinDir -Sql "CREATE USER $ProjectUser WITH PASSWORD '$escapedProj';" | Out-Null
    }
    $dbExists = Invoke-Psql -BinDir $BinDir -Sql "SELECT 1 FROM pg_database WHERE datname='$ProjectDb';"
    if ($dbExists -eq "1") {
        Invoke-Psql -BinDir $BinDir -Sql "ALTER DATABASE $ProjectDb OWNER TO $ProjectUser;" | Out-Null
    } else {
        Invoke-Psql -BinDir $BinDir -Sql "CREATE DATABASE $ProjectDb OWNER $ProjectUser;" | Out-Null
    }
    Invoke-Psql -BinDir $BinDir -Sql "GRANT ALL PRIVILEGES ON DATABASE $ProjectDb TO $ProjectUser;" | Out-Null
    Invoke-Psql -BinDir $BinDir -DbName $ProjectDb -Sql "GRANT ALL ON SCHEMA public TO $ProjectUser;" | Out-Null

    Write-Host "[7/9] Stopping service to restore pg_hba.conf" -ForegroundColor Cyan
    Stop-Service -Name $ServiceName -Force
    (Get-Service -Name $ServiceName).WaitForStatus("Stopped", "00:00:30")

    Write-Host "[8/9] Restoring original pg_hba.conf" -ForegroundColor Cyan
    Copy-Item -Path $backupPath -Destination $hbaPath -Force
    $restored = $true

    Write-Host "[9/9] Starting service in normal mode" -ForegroundColor Cyan
    Start-Service -Name $ServiceName
    Wait-PgReady -BinDir $BinDir

    Write-Host ""
    Write-Host "Verifying new postgres password..." -ForegroundColor Cyan
    Invoke-Psql -BinDir $BinDir -Password $pgPlain -Sql "SELECT 1;" | Out-Null
    Write-Host "  postgres auth OK" -ForegroundColor Green

    Write-Host "Verifying project user '$ProjectUser' on DB '$ProjectDb'..." -ForegroundColor Cyan
    Invoke-Psql -BinDir $BinDir -DbUser $ProjectUser -DbName $ProjectDb -Password $projPlain -Sql "SELECT 1;" | Out-Null
    Write-Host "  $ProjectUser auth OK" -ForegroundColor Green

    Write-Host ""
    Write-Host "Done." -ForegroundColor Green
    Write-Host "Set these in your .env (or shell):" -ForegroundColor Yellow
    Write-Host "  POSTGRES_DB=$ProjectDb"
    Write-Host "  POSTGRES_USER=$ProjectUser"
    Write-Host "  POSTGRES_PASSWORD=<the project password you just entered>"
    Write-Host "  POSTGRES_HOST=localhost"
    Write-Host "  POSTGRES_PORT=5432"
    Write-Host "  POSTGRES_SSLMODE=disable"
}
catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    if (-not $restored -and (Test-Path $backupPath)) {
        Write-Host "Restoring pg_hba.conf from backup..." -ForegroundColor Yellow
        try {
            Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
            (Get-Service -Name $ServiceName).WaitForStatus("Stopped", "00:00:30")
        } catch { }
        Copy-Item -Path $backupPath -Destination $hbaPath -Force
        Start-Service -Name $ServiceName -ErrorAction SilentlyContinue
        Write-Host "pg_hba.conf restored. Service restarted." -ForegroundColor Yellow
    }
    throw
}
finally {
    # Best-effort scrub of password variables.
    Remove-Variable pgPlain, projPlain -ErrorAction SilentlyContinue
    [System.GC]::Collect()
}
