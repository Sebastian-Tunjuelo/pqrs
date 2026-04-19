# Lanzado por start_stack.ps1 — worker Python que consume Redis y escribe síntesis en Postgres (Ollama).
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

. (Join-Path $PSScriptRoot "_resolve_python.ps1")

$env:DATABASE_URL = "postgresql://pqrs:pqrs@localhost:5433/pqrs?sslmode=disable"
$env:REDIS_URL = "redis://127.0.0.1:6379/0"
$env:OLLAMA_HOST = "http://127.0.0.1:11434"

Write-Host ""
Write-Host "=== Worker síntesis (Redis stream pqrs.summary.jobs + Ollama) ===" -ForegroundColor Cyan
Write-Host "DATABASE_URL=$env:DATABASE_URL" -ForegroundColor DarkGray
Write-Host "REDIS_URL=$env:REDIS_URL" -ForegroundColor DarkGray
Write-Host "OLLAMA_HOST=$env:OLLAMA_HOST" -ForegroundColor DarkGray
Write-Host "Ctrl+C para detener." -ForegroundColor DarkGray
Write-Host ""

$classRoot = Join-Path $Root "contexts\classification"
& $global:PqrsPythonExe -m pip install -q -e (Join-Path $Root "shared-kernel")
& $global:PqrsPythonExe -m pip install -q -e ($classRoot + "[worker]")

& $global:PqrsPythonExe -m classification.summary_redis_worker
