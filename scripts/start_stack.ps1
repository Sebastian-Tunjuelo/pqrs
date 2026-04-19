<#
.SYNOPSIS
    Levanta Docker (Postgres, Redis, Ollama) y abre dos ventanas: API Rust + Next.js dev.

.DESCRIPTION
    El navegador en http://localhost:3000 queda en blanco si Next no está corriendo.
    Este script no sustituye la primera carga de datos: si la API falla por tablas vacías,
    ejecute una vez (PowerShell, raíz del repo):

        .\scripts\verify_local.ps1

    Uso:
        .\scripts\start_stack.ps1
#>
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
$Compose = Join-Path $Root "docker-compose.yml"

function Write-Step($msg) { Write-Host "`n>>> $msg" -ForegroundColor Cyan }

Write-Host ""
Write-Host "======== PQRS: arranque (Docker + API + Next) ========" -ForegroundColor White -BackgroundColor DarkBlue
Write-Host "Raíz: $Root" -ForegroundColor Gray

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Instale Docker Desktop y asegúrese de que 'docker' esté en PATH." -ForegroundColor Red
    exit 1
}
docker info 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Inicie Docker Desktop y espere a que el motor esté listo." -ForegroundColor Red
    exit 1
}

Write-Step "1/3 Docker Compose (postgres, redis, ollama)"
docker compose -f $Compose up -d

Write-Step "2/3 Esperando Postgres (hasta ~120 s)"
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    docker compose -f $Compose exec -T postgres pg_isready -U pqrs -d pqrs 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    Start-Sleep -Seconds 2
}
if (-not $ready) {
    Write-Host "ERROR: Postgres no respondió. Revise contenedores: docker compose ps" -ForegroundColor Red
    exit 1
}

Write-Step "3/3 Abriendo API (cargo) y Next (npm) en ventanas nuevas"
$apiPs1 = Join-Path $PSScriptRoot "_run_api.ps1"
$nextPs1 = Join-Path $PSScriptRoot "_run_next.ps1"

Start-Process powershell -WorkingDirectory $Root -ArgumentList @(
    "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $apiPs1
)
Start-Sleep -Milliseconds 800
Start-Process powershell -WorkingDirectory $Root -ArgumentList @(
    "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $nextPs1
)

Write-Host ""
Write-Host "Listo." -ForegroundColor Green
Write-Host "  • Espere a que en la ventana de la API aparezca 'listening' (la primera vez cargo compila varios minutos)." -ForegroundColor Gray
Write-Host "  • En la ventana de Next verá 'Ready' y entonces recargue http://localhost:3000 en el navegador." -ForegroundColor Gray
Write-Host "  • Si la API falla por esquema/tablas: ejecute una vez  .\scripts\verify_local.ps1  y reinicie la ventana de la API." -ForegroundColor Yellow
Write-Host ""
