@echo off
REM Siembre banco_qa desde CMD (no use Get-Content: eso es PowerShell).
setlocal
cd /d "%~dp0.."
echo [*] Repo: %CD%
echo [*] Enviando data\seed\seed_banco_qa.sql al contenedor postgres...
type "data\seed\seed_banco_qa.sql" | docker compose exec -T postgres psql -U pqrs -d pqrs -v ON_ERROR_STOP=1
if errorlevel 1 (
  echo ERROR: revise que Docker este arriba ^(docker compose up -d^) y el servicio postgres.
  exit /b 1
)
echo OK: banco_qa sembrado.
