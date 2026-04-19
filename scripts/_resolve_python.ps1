# Dot-source desde otros scripts en esta carpeta:
#   . (Join-Path $PSScriptRoot "_resolve_python.ps1")
# Define: $global:PqrsPythonExe (ruta absoluta al ejecutable)

$global:PqrsPythonExe = $null

$candidates = @(
    @{ Cmd = "py";    Args = @("-3.12", "-c", "import sys; print(sys.executable)") },
    @{ Cmd = "py";    Args = @("-3.11", "-c", "import sys; print(sys.executable)") },
    @{ Cmd = "py";    Args = @("-3",    "-c", "import sys; print(sys.executable)") },
    @{ Cmd = "python"; Args = @("-c", "import sys; print(sys.executable)") },
    @{ Cmd = "python3"; Args = @("-c", "import sys; print(sys.executable)") }
)

foreach ($c in $candidates) {
    if (-not (Get-Command $c.Cmd -ErrorAction SilentlyContinue)) { continue }
    try {
        $out = & $c.Cmd @($c.Args) 2>$null
        if ($LASTEXITCODE -ne 0 -or -not ($out -match '\S')) { continue }
        $exe = ($out | Select-Object -First 1).ToString().Trim().Trim('"')
        if (-not (Test-Path -LiteralPath $exe)) { continue }
        $null = & $exe -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
        if ($LASTEXITCODE -ne 0) { continue }
        $global:PqrsPythonExe = $exe
        break
    } catch {
        continue
    }
}

if (-not $global:PqrsPythonExe) {
    Write-Host ""
    Write-Host "ERROR: No se encontró Python 3.11+ usable." -ForegroundColor Red
    Write-Host "  Probado: py -3.12, py -3.11, py -3, python, python3" -ForegroundColor Yellow
    Write-Host "  Instale Python desde https://www.python.org/downloads/windows/ y marque 'Add python.exe to PATH'." -ForegroundColor Yellow
    Write-Host ""
    throw "PqrsPythonExe: no resolver"
}
