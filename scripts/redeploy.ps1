# =============================================================================
# redeploy.ps1 — Reinicia ngrok y actualiza Vercel con la nueva URL pública
# Uso: .\scripts\redeploy.ps1
# =============================================================================

$ErrorActionPreference = "Stop"

$VERCEL_TOKEN = $env:VERCEL_TOKEN
if (-not $VERCEL_TOKEN) {
    Write-Host "ERROR: Define la variable VERCEL_TOKEN antes de correr este script." -ForegroundColor Red
    Write-Host "  Ejemplo: `$env:VERCEL_TOKEN = 'tu_token_aqui'" -ForegroundColor Yellow
    exit 1
}
$NGROK_PATH   = "C:\ngrok\ngrok.exe"
$PRESENTATION = "contexts\presentation"

# ── 1. Verificar que la API Rust está corriendo ───────────────────────────────
Write-Host "`n==> Verificando API Rust en :8080..." -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod "http://127.0.0.1:8080/api/v1/health" -ErrorAction Stop
    Write-Host "    API OK — status: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "    ERROR: La API Rust no está corriendo en :8080." -ForegroundColor Red
    Write-Host "    Ejecuta primero: cd contexts\api && cargo run" -ForegroundColor Yellow
    exit 1
}

# ── 2. Matar ngrok anterior si existe ────────────────────────────────────────
Write-Host "`n==> Deteniendo ngrok anterior (si existe)..." -ForegroundColor Cyan
Get-Process -Name "ngrok" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

# ── 3. Arrancar ngrok en background ──────────────────────────────────────────
Write-Host "`n==> Iniciando ngrok en puerto 8080..." -ForegroundColor Cyan
Start-Process -FilePath $NGROK_PATH -ArgumentList "http 8080 --log=stdout" -WindowStyle Hidden
Start-Sleep -Seconds 4

# ── 4. Obtener URL pública de ngrok ──────────────────────────────────────────
Write-Host "`n==> Obteniendo URL pública de ngrok..." -ForegroundColor Cyan
$maxRetries = 10
$ngrokUrl = $null
for ($i = 0; $i -lt $maxRetries; $i++) {
    try {
        $tunnels = Invoke-RestMethod "http://127.0.0.1:4040/api/tunnels" -ErrorAction Stop
        $ngrokUrl = ($tunnels.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1).public_url
        if ($ngrokUrl) { break }
    } catch {}
    Start-Sleep -Seconds 1
}

if (-not $ngrokUrl) {
    Write-Host "    ERROR: No se pudo obtener la URL de ngrok." -ForegroundColor Red
    exit 1
}
Write-Host "    URL pública: $ngrokUrl" -ForegroundColor Green

# ── 5. Verificar que la API es accesible desde internet ──────────────────────
Write-Host "`n==> Verificando acceso externo a la API..." -ForegroundColor Cyan
try {
    $ext = Invoke-RestMethod "$ngrokUrl/api/v1/health" -Headers @{"ngrok-skip-browser-warning"="true"} -ErrorAction Stop
    Write-Host "    Acceso externo OK — status: $($ext.status)" -ForegroundColor Green
} catch {
    Write-Host "    ADVERTENCIA: La API no responde desde internet aún. Continúa de todas formas." -ForegroundColor Yellow
}

# ── 6. Actualizar variables de entorno en Vercel ─────────────────────────────
Write-Host "`n==> Actualizando variables en Vercel..." -ForegroundColor Cyan
$env:PATH += ";$env:APPDATA\npm"

foreach ($varName in @("NEXT_PUBLIC_API_URL", "API_URL")) {
    try {
        echo "y" | vercel env rm $varName production --token $VERCEL_TOKEN --cwd $PRESENTATION --yes 2>&1 | Out-Null
    } catch {}
    $ngrokUrl | vercel env add $varName production --token $VERCEL_TOKEN --cwd $PRESENTATION 2>&1 | Out-Null
    Write-Host "    $varName=$ngrokUrl" -ForegroundColor Green
}

# ── 7. Redesplegar en Vercel producción ──────────────────────────────────────
Write-Host "`n==> Desplegando en Vercel (producción)..." -ForegroundColor Cyan
$deployOutput = vercel --prod --token $VERCEL_TOKEN --yes --cwd $PRESENTATION 2>&1
$prodUrl = ($deployOutput | Select-String "https://presentation-theta-one.vercel.app").Matches.Value
if (-not $prodUrl) {
    $prodUrl = "https://presentation-theta-one.vercel.app"
}
Write-Host "    Deploy OK" -ForegroundColor Green

# ── 8. Actualizar .env.local del bot con la nueva URL ────────────────────────
Write-Host "`n==> Actualizando PQRS_API_URL en el bot de Telegram..." -ForegroundColor Cyan
$botEnv = "contexts\telegram_bot\.env"
$content = Get-Content $botEnv
$content = $content -replace "^PQRS_API_URL=.*", "PQRS_API_URL=$ngrokUrl/api/v1"
Set-Content $botEnv $content
Write-Host "    Bot .env actualizado" -ForegroundColor Green

# ── Resumen ───────────────────────────────────────────────────────────────────
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  DESPLIEGUE COMPLETADO" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Frontend:  $prodUrl"
Write-Host "  API:       $ngrokUrl/api/v1"
Write-Host "  Bot:       @AlcaldiaMedellinPQRSD_bot"
Write-Host ""
Write-Host "  NOTA: Reinicia el bot de Telegram para que use la nueva URL:" -ForegroundColor Yellow
Write-Host "  cd contexts\telegram_bot && py -3.11 bot.py" -ForegroundColor Yellow
Write-Host "============================================`n" -ForegroundColor Cyan
