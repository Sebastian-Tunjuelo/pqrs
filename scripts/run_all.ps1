<#
.SYNOPSIS
    Corre todo en local: Docker + DB + seeds + demo + pytest + cargo test + build Next.

.DESCRIPTION
    Use PowerShell (no CMD). Desde la raíz del repo:
        .\scripts\run_all.ps1

    O haga doble clic en scripts\run_all.cmd

    Requisitos: Docker Desktop en ejecución, Python 3.11+, Rust (cargo), Node/npm (para build frontend).
#>
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

. (Join-Path $PSScriptRoot "_resolve_python.ps1")

function Write-Banner($msg) {
    Write-Host ""
    Write-Host ">>> $msg" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "======== PQRS: corre todo ========" -ForegroundColor White -BackgroundColor DarkBlue
Write-Host "Raíz: $Root" -ForegroundColor Gray
Write-Host "Python: $global:PqrsPythonExe" -ForegroundColor Gray
Write-Host ""

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: 'docker' no está en PATH. Instale Docker Desktop." -ForegroundColor Red
    exit 1
}
docker info 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker no responde. Abra Docker Desktop y espere hasta 'Engine running'." -ForegroundColor Red
    exit 1
}

Write-Banner "1/4 Infra + base de datos (verify_local.ps1)"
& (Join-Path $PSScriptRoot "verify_local.ps1")
if ($LASTEXITCODE -ne 0) {
    Write-Host "verify_local falló con código $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Banner "2/4 pip install -e (paquetes con tests)"
$editable = @(
    "shared-kernel",
    "contexts\ingestion",
    "contexts\warehouse",
    "contexts\routing",
    "contexts\prioritization",
    "contexts\classification",
    "orchestration",
    "e2e"
)
foreach ($rel in $editable) {
    $p = Join-Path $Root $rel
    if (-not (Test-Path $p)) { continue }
    & $global:PqrsPythonExe -m pip install -q -e $p
}

Write-Banner "3/4 pytest (cada paquete; evita choque del nombre 'tests')"
$testRoots = @(
    @{ Path = "shared-kernel";       Dir = "tests" },
    @{ Path = "contexts\ingestion";  Dir = "tests" },
    @{ Path = "contexts\warehouse";  Dir = "tests" },
    @{ Path = "contexts\routing";   Dir = "tests" },
    @{ Path = "contexts\prioritization"; Dir = "tests" },
    @{ Path = "contexts\classification"; Dir = "tests" },
    @{ Path = "orchestration";       Dir = "tests" }
)
foreach ($t in $testRoots) {
    $here = Join-Path $Root $t.Path
    if (-not (Test-Path (Join-Path $here $t.Dir))) { continue }
    Push-Location $here
    try {
        Write-Host "  pytest $($t.Path) ..." -ForegroundColor DarkGray
        & $global:PqrsPythonExe -m pytest $t.Dir -q --tb=line
        if ($LASTEXITCODE -ne 0) { throw "pytest falló en $($t.Path)" }
    } finally {
        Pop-Location
    }
}
Push-Location (Join-Path $Root "e2e")
try {
    Write-Host "  pytest e2e ..." -ForegroundColor DarkGray
    & $global:PqrsPythonExe -m pytest tests -q --tb=line -m e2e
    if ($LASTEXITCODE -ne 0) { throw "pytest e2e falló" }
} finally {
    Pop-Location
}

Write-Banner "4/4 Rust (API) + Next.js (build)"
$env:DATABASE_URL = "postgresql://pqrs:pqrs@localhost:5433/pqrs"
if (Get-Command cargo -ErrorAction SilentlyContinue) {
    Push-Location (Join-Path $Root "contexts\api")
    try {
        cargo test -q
        if ($LASTEXITCODE -ne 0) { throw "cargo test falló" }
    } finally {
        Pop-Location
    }
} else {
    Write-Host "  (omitido) cargo no está en PATH" -ForegroundColor Yellow
}

if (Get-Command npm -ErrorAction SilentlyContinue) {
    Push-Location (Join-Path $Root "contexts\presentation")
    try {
        if (-not (Test-Path "node_modules")) {
            npm ci
            if ($LASTEXITCODE -ne 0) { throw "npm ci falló" }
        }
        npm run build
        if ($LASTEXITCODE -ne 0) { throw "npm run build falló" }
    } finally {
        Pop-Location
    }
} else {
    Write-Host "  (omitido) npm no está en PATH" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======== Listo: todo pasó ========" -ForegroundColor White -BackgroundColor DarkGreen
Write-Host ""
