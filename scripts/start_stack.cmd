@echo off
cd /d "%~dp0.."
echo Arranque PQRS: Docker + ventanas API y Next...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_stack.ps1"
echo.
pause
