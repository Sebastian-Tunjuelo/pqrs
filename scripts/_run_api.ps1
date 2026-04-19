# Lanzado por start_stack.ps1 — no hace falta ejecutarlo a mano salvo depuración.
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location (Join-Path $Root "contexts\api")
$env:DATABASE_URL = "postgresql://pqrs:pqrs@localhost:5433/pqrs?sslmode=disable"
$env:REDIS_URL = "redis://127.0.0.1:6379/0"
if (-not $env:PORT) { $env:PORT = "8080" }
Write-Host ""
Write-Host "=== API Rust (Axum) — http://127.0.0.1:$($env:PORT) ===" -ForegroundColor Cyan
Write-Host "DATABASE_URL=$env:DATABASE_URL" -ForegroundColor DarkGray
Write-Host "REDIS_URL=$env:REDIS_URL (síntesis bajo demanda vía worker Python)" -ForegroundColor DarkGray
Write-Host "Ctrl+C para detener." -ForegroundColor DarkGray
Write-Host ""
cargo run
