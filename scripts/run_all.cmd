@echo off
setlocal
cd /d "%~dp0.."
echo.
echo === PQRS run_all (PowerShell) ===
echo Carpeta: %CD%
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_all.ps1"
set ERR=%ERRORLEVEL%
echo.
if %ERR% neq 0 (
  echo ERROR: salida %ERR%
) else (
  echo OK.
)
pause
endlocal
exit /b %ERR%
