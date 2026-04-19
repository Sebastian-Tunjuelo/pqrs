@echo off
REM Compila la API Rust con el linker MSVC (requiere VS Build Tools 2022).
call "%ProgramFiles(x86)%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
cd /d "%~dp0..\contexts\api"
cargo %*
