# Lanzado por start_stack.ps1 — no hace falta ejecutarlo a mano salvo depuración.
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Pres = Join-Path $Root "contexts\presentation"
Set-Location $Pres

$envLocal = Join-Path $Pres ".env.local"
if (-not (Test-Path $envLocal)) {
    @"
NEXT_PUBLIC_API_URL=http://127.0.0.1:8080
"@ | Set-Content -LiteralPath $envLocal -Encoding utf8
    Write-Host "Creado .env.local con NEXT_PUBLIC_API_URL=http://127.0.0.1:8080" -ForegroundColor Green
}

if (-not (Test-Path (Join-Path $Pres "node_modules"))) {
    Write-Host "Instalando dependencias (npm ci)..." -ForegroundColor Yellow
    npm ci
}

# Si quedó un `next dev` colgado, libera el puerto 3000 (evita EADDRINUSE).
Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
    $owning = $_.OwningProcess
    $name = (Get-Process -Id $owning -ErrorAction SilentlyContinue).ProcessName
    if ($name -eq "node") {
        Write-Host "Cerrando Node previo en puerto 3000 (PID $owning)..." -ForegroundColor Yellow
        Stop-Process -Id $owning -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep -Milliseconds 400

Write-Host ""
Write-Host "=== Next.js — http://localhost:3000 ===" -ForegroundColor Cyan
Write-Host "Ctrl+C para detener." -ForegroundColor DarkGray
Write-Host ""
npm run dev
