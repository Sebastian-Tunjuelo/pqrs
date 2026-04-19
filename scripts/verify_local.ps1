<#
.SYNOPSIS
    Prueba la pila local: Docker → Alembic → seeds SQL → demo 200 PQRS → (opcional) health API.

.DESCRIPTION
    Ejecutar desde la raíz del repo en PowerShell:
        .\scripts\verify_local.ps1

    O el flujo completo (tests + build):
        .\scripts\run_all.ps1
        scripts\run_all.cmd

    Para ver la web (API + Next en ventanas aparte), tras tener la BD lista:
        .\scripts\start_stack.ps1
        scripts\start_stack.cmd

    Requisitos: Docker Desktop, Python 3.11+ (py o python en PATH), imagen postgis/postgis (primera vez: descarga grande).

    No inicia la API Rust ni Next.js por sí mismo; use start_stack o los comandos al final.
#>
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

. (Join-Path $PSScriptRoot "_resolve_python.ps1")
Write-Host "Python usado: $global:PqrsPythonExe" -ForegroundColor DarkGray

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }

Write-Step "1. Docker Compose (postgres, redis, ollama)"
docker compose -f (Join-Path $Root "docker-compose.yml") up -d

Write-Step "2. Esperando Postgres (hasta ~120 s)"
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    docker compose exec -T postgres pg_isready -U pqrs -d pqrs 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    Start-Sleep -Seconds 2
}
if (-not $ready) {
    Write-Error "Postgres no respondió. Revise Docker Desktop y volver a ejecutar."
}

Write-Step "2b. Limpiar stream Redis pqrs.summary.jobs (UUIDs viejos tras purge demo)"
docker compose -f (Join-Path $Root "docker-compose.yml") exec -T redis redis-cli DEL pqrs.summary.jobs 2>$null | Out-Null

Write-Step "3. Instalar warehouse + Alembic"
& $global:PqrsPythonExe -m pip install -q -e (Join-Path $Root "contexts\warehouse")

$env:DATABASE_URL = "postgresql+psycopg://pqrs:pqrs@localhost:5433/pqrs"
Push-Location (Join-Path $Root "contexts\warehouse")
try {
    & $global:PqrsPythonExe -m alembic upgrade head
} finally {
    Pop-Location
}

Write-Step "4. Seeds dim_secretaria y dim_territorio (puede tardar si el SQL es grande)"
# UTF-8: sin esto, en Windows los acentos de los SQL pueden corromperse al pipear a psql.
Get-Content (Join-Path $Root "data\seed\seed_dim_secretaria.sql") -Raw -Encoding utf8 |
    docker compose exec -T postgres psql -U pqrs -d pqrs -v ON_ERROR_STOP=1
Get-Content (Join-Path $Root "data\seed\seed_dim_territorio.sql") -Raw -Encoding utf8 |
    docker compose exec -T postgres psql -U pqrs -d pqrs -v ON_ERROR_STOP=1

Write-Step "5. Demo 200 PQRS sintéticas"
$env:DATABASE_URL = "postgresql://pqrs:pqrs@localhost:5433/pqrs?sslmode=disable"
& $global:PqrsPythonExe -m pip install -q -r (Join-Path $Root "scripts\requirements-demo.txt")
& $global:PqrsPythonExe (Join-Path $Root "scripts\demo_seed_pqrs.py") --purge

Write-Step "6. Comprobar API (opcional)"
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8080/api/v1/health" -UseBasicParsing -TimeoutSec 3
    Write-Host "API respondió: $($r.StatusCode) $($r.Content)" -ForegroundColor Green
} catch {
    Write-Host "API no está en 8080. Para probarla:" -ForegroundColor Yellow
    Write-Host '  cd contexts\api' -ForegroundColor Gray
    Write-Host '  set DATABASE_URL=postgresql://pqrs:pqrs@localhost:5433/pqrs?sslmode=disable' -ForegroundColor Gray
    Write-Host '  cargo run' -ForegroundColor Gray
}

Write-Step "7. E2E (requiere API arriba)"
Write-Host '  pip install -e .\e2e' -ForegroundColor Gray
Write-Host "  & `"$global:PqrsPythonExe`" -m pytest .\e2e\tests -q -m e2e" -ForegroundColor Gray

Write-Host "`nListo: Postgres tiene esquema, dimensiones y ~200 PQRS demo." -ForegroundColor Green
